import json
import logging
from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundError, ValidationError
from app.intelligence.context import LeadAIContextBuilder
from app.llm.models import LLMCompletionRequest, LLMMessage, LLMRole
from app.llm.service import LLMService
from app.pitch.prompts import (
    PITCH_REPAIR_PROMPT,
    PITCH_SYSTEM_PROMPT,
    PITCH_USER_PROMPT_TEMPLATE,
)
from app.pitch.schemas import (
    PitchGenerationRequest,
    PitchGenerationResponse,
    PitchLLMOutput,
)
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.repositories.outreach import OutreachRepository
from app.schemas.agent_run import AgentRun
from app.schemas.enums import (
    AgentRunStatus,
    AgentType,
    LeadStatus,
    OutreachChannel,
    OutreachDirection,
    OutreachMessageType,
    OutreachStatus,
    ServiceType,
)
from app.schemas.lead import Lead
from app.schemas.outreach import Outreach
from app.services.agent_run import AgentRunService
from app.services.ai_generation import AIGenerationService
from app.services.outreach import OutreachService

logger = logging.getLogger(__name__)


class PitchGenerationService:
    """
    Orchestrates evidence-grounded personalized outreach pitch generation.
    Creates Outreach records strictly in DRAFT status. Prevents duplicate drafts.
    """

    def __init__(
        self,
        lead_repo: Optional[LeadRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
        outreach_service: Optional[OutreachService] = None,
        outreach_repo: Optional[OutreachRepository] = None,
        context_builder: Optional[LeadAIContextBuilder] = None,
        llm_service: Optional[LLMService] = None,
        ai_gen_service: Optional[AIGenerationService] = None,
        agent_run_service: Optional[AgentRunService] = None,
    ):
        self.lead_repo = lead_repo or LeadRepository()
        self.business_repo = business_repo or BusinessRepository()
        self.outreach_repo = outreach_repo or OutreachRepository()
        self.outreach_service = outreach_service or OutreachService(
            outreach_repo=self.outreach_repo,
            lead_repo=self.lead_repo,
            business_repo=self.business_repo,
        )
        self.context_builder = context_builder or LeadAIContextBuilder(
            lead_repo=self.lead_repo, business_repo=self.business_repo
        )
        self.ai_gen_service = ai_gen_service or AIGenerationService()
        self.llm_service = llm_service or LLMService(ai_generation_service=self.ai_gen_service)
        self.agent_run_service = agent_run_service or AgentRunService()
    async def generate_pitch(
        self, lead_id: str, req: Optional[PitchGenerationRequest] = None
    ) -> PitchGenerationResponse:
        request_config = req or PitchGenerationRequest()

        lead_doc = await self.lead_repo.get_by_id(lead_id)
        if not lead_doc:
            raise NotFoundError(f"Lead with ID '{lead_id}' not found.")
        lead = Lead(**lead_doc)

        if lead.lead_status == LeadStatus.DO_NOT_CONTACT:
            raise ValidationError("Lead status is DO_NOT_CONTACT. Pitch generation is blocked.")
        if lead.lead_status == LeadStatus.INVALID:
            raise ValidationError("Lead status is INVALID. Pitch generation is blocked.")

        biz_id_str = str(lead.business_id)

        if not request_config.force_refresh:
            existing_outreaches = await self.outreach_repo.list_by_lead_id(lead_id)
            for out_dict in existing_outreaches:
                out_obj = Outreach(**out_dict)
                if (
                    out_obj.channel == request_config.channel
                    and out_obj.message_type == request_config.message_type
                    and out_obj.status in (OutreachStatus.DRAFT, OutreachStatus.READY)
                ):
                    return PitchGenerationResponse(
                        lead_id=lead_id,
                        business_id=biz_id_str,
                        outreach_id=str(out_obj.id),
                        channel=out_obj.channel,
                        message_type=out_obj.message_type,
                        subject=out_obj.subject,
                        body=out_obj.message,
                        personalization_points=[],
                        evidence_used=[],
                        recommended_service=ServiceType.UNKNOWN,
                        confidence=0.9,
                        status=out_obj.status,
                    )

        context_dict = await self.context_builder.build_context(lead_id)
        context_json = json.dumps(context_dict, indent=2)

        agent_run = await self.agent_run_service.create_run(
            AgentRun(
                agent_type=AgentType.PITCH_GENERATION,
                status=AgentRunStatus.RUNNING,
                lead_id=self.lead_repo.parse_object_id(lead_id),
                business_id=self.business_repo.parse_object_id(biz_id_str),
                input_reference=f"lead_id={lead_id}, channel={request_config.channel.value}",
            )
        )
        run_id = str(agent_run.id) if agent_run and agent_run.id else None

        system_msg = LLMMessage(role=LLMRole.SYSTEM, content=PITCH_SYSTEM_PROMPT)
        user_msg = LLMMessage(
            role=LLMRole.USER,
            content=PITCH_USER_PROMPT_TEMPLATE.format(
                channel=request_config.channel.value,
                message_type=request_config.message_type.value,
                context_json=context_json,
            ),
        )

        try:
            llm_res = await self.llm_service.generate(
                LLMCompletionRequest(
                    messages=[system_msg, user_msg],
                    temperature=0.7,
                    task_type="pitch_generation",
                    model=request_config.model,
                )
            )

            pitch_output, was_repaired = await self._parse_and_validate(
                llm_res.content, [system_msg, user_msg], request_config.model
            )

            subject_val = pitch_output.subject if request_config.channel == OutreachChannel.EMAIL else None

            outreach_obj = Outreach(
                lead_id=self.outreach_repo.parse_object_id(lead_id),
                business_id=self.outreach_repo.parse_object_id(biz_id_str),
                channel=request_config.channel,
                direction=OutreachDirection.OUTBOUND,
                message_type=request_config.message_type,
                subject=subject_val,
                message=pitch_output.body,
                generated_by="AI_PITCH_GENERATOR",
                status=OutreachStatus.DRAFT,
            )

            created_doc = await self.outreach_repo.create(
                outreach_obj.model_dump(by_alias=True, exclude={"id"})
            )
            created_outreach = Outreach(**created_doc)
            outreach_id_str = str(created_outreach.id)

            if run_id:
                await self.agent_run_service.run_repo.update_by_id(
                    run_id,
                    {
                        "status": AgentRunStatus.COMPLETED.value,
                        "output_data": {"outreach_id": outreach_id_str},
                    },
                )

            return PitchGenerationResponse(
                lead_id=lead_id,
                business_id=biz_id_str,
                outreach_id=outreach_id_str,
                channel=request_config.channel,
                message_type=request_config.message_type,
                subject=subject_val,
                body=pitch_output.body,
                personalization_points=pitch_output.personalization_points,
                evidence_used=pitch_output.evidence_used,
                recommended_service=pitch_output.recommended_service,
                confidence=pitch_output.confidence,
                status=OutreachStatus.DRAFT,
                run_id=run_id,
            )

        except Exception as exc:
            logger.error(f"Pitch generation failed for lead {lead_id}: {exc}")
            if run_id:
                try:
                    await self.agent_run_service.run_repo.update_by_id(
                        run_id,
                        {"status": AgentRunStatus.FAILED.value, "error_message": str(exc)},
                    )
                except Exception:
                    pass
            raise exc

    async def _parse_and_validate(
        self, raw_content: str, conversation: List[LLMMessage], model_override: Optional[str]
    ) -> tuple[PitchLLMOutput, bool]:
        parsed = self._extract_json(raw_content)
        if parsed:
            try:
                out = PitchLLMOutput.model_validate(parsed)
                return out, False
            except Exception as e:
                logger.warning(f"Initial LLM pitch output validation failed: {e}")

        logger.info("Attempting single repair for LLM pitch output...")
        repair_msg = LLMMessage(role=LLMRole.USER, content=PITCH_REPAIR_PROMPT)
        repair_conv = conversation + [LLMMessage(role=LLMRole.ASSISTANT, content=raw_content), repair_msg]

        repair_res = await self.llm_service.generate(
            LLMCompletionRequest(
                messages=repair_conv,
                temperature=0.0,
                task_type="pitch_generation_repair",
                model=model_override,
            )
        )

        repaired_parsed = self._extract_json(repair_res.content)
        if repaired_parsed:
            try:
                out = PitchLLMOutput.model_validate(repaired_parsed)
                return out, True
            except Exception as exc:
                logger.error(f"Repaired LLM pitch output validation failed: {exc}")

        raise ValidationError("Failed to produce structured JSON pitch result from LLM.")

    def _extract_json(self, text: str) -> Optional[Dict[str, Any]]:
        text_str = text.strip()
        if text_str.startswith("```"):
            lines = text_str.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            text_str = "\n".join(lines).strip()

        try:
            return json.loads(text_str)
        except Exception:
            start_idx = text_str.find("{")
            end_idx = text_str.rfind("}")
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                try:
                    return json.loads(text_str[start_idx : end_idx + 1])
                except Exception:
                    pass
        return None
