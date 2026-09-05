import logging
import time
from typing import Any, Dict, Optional
import httpx
from app.core.config import Settings, settings
from app.llm.client import OmniRouteClient
from app.llm.exceptions import (
    LLMConfigurationError,
    LLMError,
    sanitize_error_message,
)
from app.llm.models import LLMCompletionRequest, LLMCompletionResponse
from app.schemas.ai_generation import AIGeneration
from app.schemas.enums import AIGenerationValidation
from app.services.ai_generation import AIGenerationService

logger = logging.getLogger(__name__)


class LLMService:
    """
    Application-level service for orchestrating LLM requests, response normalization,
    configuration validation, and AI generation audit logging.
    """

    def __init__(
        self,
        client: Optional[OmniRouteClient] = None,
        config: Optional[Settings] = None,
        ai_generation_service: Optional[AIGenerationService] = None,
    ):
        self.config = config or settings
        self.client = client or OmniRouteClient(
            base_url=self.config.omniroute_base_url,
            api_key=self.config.omniroute_api_key,
            timeout_seconds=self.config.omniroute_timeout_seconds,
            max_retries=self.config.omniroute_max_retries,
        )
        self.ai_generation_service = ai_generation_service

    async def generate(self, request: LLMCompletionRequest) -> LLMCompletionResponse:
        if not self.config.is_omniroute_configured():
            raise LLMConfigurationError(
                "OmniRoute is not configured or configured with placeholder credentials."
            )

        selected_model = request.model or self.config.omniroute_default_model
        if not selected_model or selected_model.startswith("YOUR_"):
            raise LLMConfigurationError(
                "No valid default or requested model configured for OmniRoute."
            )

        task_type = request.task_type or "generic"
        start_time = time.time()

        try:
            response = await self.client.create_chat_completion(request, selected_model)
            latency_ms = int((time.time() - start_time) * 1000)

            logger.info(
                f"LLM generation completed successfully [task={task_type}, model={selected_model}, latency={latency_ms}ms]"
            )

            if self.ai_generation_service:
                try:
                    gen_doc = AIGeneration(
                        task_type=task_type,
                        provider="omniroute",
                        model=selected_model,
                        output_text=response.content,
                        structured_output={"finish_reason": response.finish_reason},
                        validation_status=AIGenerationValidation.VALID,
                        tokens_input=response.usage.prompt_tokens if response.usage else None,
                        tokens_output=response.usage.completion_tokens if response.usage else None,
                        latency_ms=latency_ms,
                    )
                    await self.ai_generation_service.create_generation(gen_doc)
                except Exception as audit_exc:
                    logger.warning(f"Failed to record AI generation log: {sanitize_error_message(str(audit_exc))}")

            return response

        except LLMError as exc:
            latency_ms = int((time.time() - start_time) * 1000)
            safe_err = sanitize_error_message(str(exc))
            logger.error(f"LLM request failed [task={task_type}, model={selected_model}]: {safe_err}")

            if self.ai_generation_service:
                try:
                    gen_doc = AIGeneration(
                        task_type=task_type,
                        provider="omniroute",
                        model=selected_model,
                        output_text=None,
                        structured_output={"error": safe_err},
                        validation_status=AIGenerationValidation.INVALID,
                        latency_ms=latency_ms,
                    )
                    await self.ai_generation_service.create_generation(gen_doc)
                except Exception:
                    pass

            raise exc

    async def health_check(self) -> Dict[str, Any]:
        base_url = self.config.omniroute_base_url.rstrip("/")
        if not self.config.is_omniroute_configured():
            return {
                "status": "degraded",
                "provider": "omniroute",
                "reason": "OmniRoute configuration missing or using placeholder credentials.",
            }

        endpoint = f"{base_url}/models"
        headers = {}
        if self.config.omniroute_api_key:
            headers["Authorization"] = f"Bearer {self.config.omniroute_api_key}"

        try:
            async with httpx.AsyncClient() as http_client:
                res = await http_client.get(endpoint, headers=headers, timeout=5.0)
                if res.status_code in (200, 401, 403, 404):
                    status_str = "ok" if res.status_code == 200 else "degraded"
                    return {
                        "status": status_str,
                        "provider": "omniroute",
                        "base_url": base_url,
                        "http_status": res.status_code,
                    }
                else:
                    return {
                        "status": "degraded",
                        "provider": "omniroute",
                        "http_status": res.status_code,
                    }
        except Exception as exc:
            safe_reason = sanitize_error_message(str(exc))
            return {
                "status": "unavailable",
                "provider": "omniroute",
                "reason": safe_reason,
            }
