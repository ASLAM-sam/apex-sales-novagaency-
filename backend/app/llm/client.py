import asyncio
import logging
from typing import Any, Dict, Optional
import httpx
from app.llm.exceptions import (
    LLMAuthenticationError,
    LLMConnectionError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUpstreamError,
    sanitize_error_message,
)
from app.llm.models import LLMCompletionRequest, LLMCompletionResponse, LLMTokenUsage

logger = logging.getLogger(__name__)


class OmniRouteClient:
    """
    OpenAI-compatible HTTP client for communicating with the OmniRoute LLM gateway.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:20128/v1",
        api_key: str = "",
        timeout_seconds: int = 60,
        max_retries: int = 2,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_seconds = timeout_seconds
        self.max_retries = max_retries
        self._custom_client = http_client

    def _get_headers(self) -> Dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    async def create_chat_completion(
        self, request: LLMCompletionRequest, model: str
    ) -> LLMCompletionResponse:
        endpoint = f"{self.base_url}/chat/completions"
        payload: Dict[str, Any] = {
            "model": model,
            "messages": [
                {"role": msg.role.value if hasattr(msg.role, "value") else str(msg.role), "content": msg.content}
                for msg in request.messages
            ],
        }

        if request.temperature is not None:
            payload["temperature"] = request.temperature
        if request.max_tokens is not None:
            payload["max_tokens"] = request.max_tokens

        last_exception: Optional[Exception] = None
        total_attempts = 1 + max(0, self.max_retries)

        for attempt in range(1, total_attempts + 1):
            try:
                return await self._execute_request(endpoint, payload)
            except (LLMAuthenticationError, LLMRateLimitError) as e:
                raise e
            except (LLMTimeoutError, LLMConnectionError, LLMUpstreamError) as e:
                last_exception = e
                if attempt < total_attempts:
                    retry_delay = 0.5 * (2 ** (attempt - 1))
                    logger.warning(
                        f"OmniRoute request attempt {attempt}/{total_attempts} failed ({e.__class__.__name__}). Retrying in {retry_delay}s..."
                    )
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error(f"OmniRoute request failed after {total_attempts} attempts.")
                    raise e
            except Exception as e:
                safe_msg = sanitize_error_message(str(e))
                raise LLMUpstreamError(f"Unexpected OmniRoute client error: {safe_msg}") from e

        if last_exception:
            raise last_exception
        raise LLMUpstreamError("OmniRoute request failed unexpectedly.")

    async def _execute_request(
        self, endpoint: str, payload: Dict[str, Any]
    ) -> LLMCompletionResponse:
        headers = self._get_headers()
        timeout = httpx.Timeout(float(self.timeout_seconds))

        try:
            if self._custom_client:
                response = await self._custom_client.post(
                    endpoint, json=payload, headers=headers, timeout=timeout
                )
            else:
                async with httpx.AsyncClient() as client:
                    response = await client.post(
                        endpoint, json=payload, headers=headers, timeout=timeout
                    )
        except httpx.TimeoutException as exc:
            raise LLMTimeoutError(
                f"OmniRoute LLM request timed out after {self.timeout_seconds} seconds."
            ) from exc
        except (httpx.ConnectError, httpx.NetworkError) as exc:
            raise LLMConnectionError(
                "Failed to establish connection to OmniRoute LLM gateway."
            ) from exc
        except httpx.RequestError as exc:
            safe_msg = sanitize_error_message(str(exc))
            raise LLMConnectionError(
                f"OmniRoute HTTP request failed: {safe_msg}"
            ) from exc

        status = response.status_code

        if status in (401, 403):
            raise LLMAuthenticationError(
                "OmniRoute authentication failed: Invalid or unauthorized API key."
            )
        elif status == 429:
            raise LLMRateLimitError("OmniRoute rate limit exceeded.")
        elif status >= 500:
            raise LLMUpstreamError(
                f"OmniRoute gateway returned upstream server error HTTP {status}."
            )
        elif status >= 400:
            raise LLMUpstreamError(
                f"OmniRoute gateway returned client error HTTP {status}."
            )

        try:
            data = response.json()
        except Exception as exc:
            raise LLMUpstreamError(
                "Failed to parse JSON response from OmniRoute gateway."
            ) from exc

        return self._normalize_response(data, fallback_model=payload.get("model", "unknown"))

    def _normalize_response(
        self, data: Dict[str, Any], fallback_model: str
    ) -> LLMCompletionResponse:
        if not isinstance(data, dict):
            raise LLMUpstreamError("Invalid response schema from OmniRoute: expected JSON object.")

        choices = data.get("choices")
        if not choices or not isinstance(choices, list) or len(choices) == 0:
            raise LLMUpstreamError("OmniRoute response contained no choices.")

        first_choice = choices[0]
        if not isinstance(first_choice, dict):
            raise LLMUpstreamError("Invalid choice format in OmniRoute response.")

        message_obj = first_choice.get("message", {})
        if isinstance(message_obj, dict):
            content = message_obj.get("content", "")
        else:
            content = str(message_obj)

        if content is None:
            content = ""

        model_name = data.get("model") or fallback_model
        finish_reason = first_choice.get("finish_reason") or "stop"

        usage_data = data.get("usage")
        token_usage: Optional[LLMTokenUsage] = None

        if isinstance(usage_data, dict):
            token_usage = LLMTokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens"),
                completion_tokens=usage_data.get("completion_tokens"),
                total_tokens=usage_data.get("total_tokens"),
            )

        return LLMCompletionResponse(
            content=content,
            model=model_name,
            finish_reason=finish_reason,
            usage=token_usage,
            raw_response=data,
        )
