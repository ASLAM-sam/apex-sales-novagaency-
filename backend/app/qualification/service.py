import json
import logging
from typing import Any, Dict, List, Optional
from app.core.exceptions import NotFoundError, ValidationError
from app.intelligence.context import LeadAIContextBuilder
from app.llm.models import LLMCompletionRequest, LLMMessage, LLMRole
from app.llm.service import LLMService
from app.qualification.prompts import (
    QUALIFICATION_REPAIR_PROMPT,
    QUALIFICATION_SYSTEM_PROMPT,
    QUALIFICATION_USER_PROMPT_TEMPLATE,
)
from app.qualification.schemas import (
    LeadQualificationRequest,
    LeadQualificationResponse,
    QualificationLLMOutput,
)
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.schemas.agent_run import AgentRun
from app.schemas.enums import (
    AgentRunStatus,
    AgentType,
    EvidenceType,
    LeadStatus,
    PipelineStage,
    ServiceType,
)
from app.schemas.lead import Evidence, Lead, ServiceOpportunity
from app.services.agent_run import AgentRunService
from app.services.ai_generation import AIGenerationService

logger = logging.getLogger(__name__)


class LeadQualificationService:
    def __init__(
        self,
        lead_repo: Optional[LeadRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
        context_builder: Optional[LeadAIContextBuilder] = None,
        llm_service: Optional[LLMService] = None,
        ai_gen_service: Optional[AIGenerationService] = None,
        agent_run_service: Optional[AgentRunService] = None,
    ):
        self.lead_repo = lead_repo or LeadRepository()
        self.business_repo = business_repo or BusinessRepository()
        self.context_builder = context_builder or LeadAIContextBuilder(
            lead_repo=self.lead_repo, business_repo=self.business_repo
        )
        self.ai_gen_service = ai_gen_service or AIGenerationService()
        self.llm_service = llm_service or LLMService(ai_generation_service=self.ai_gen_service)
        self.agent_run_service = agent_run_service or AgentRunService()
    async def qualify_lead(
        self, lead_id: str, req: Optional[LeadQualificationRequest] = None
    ) -> LeadQualificationResponse:
        lead_doc = await self.lead_repo.get_by_id(lead_id)
        if not lead_doc:
            raise NotFoundError(f"Lead with ID '{lead_id}' not found.")
        lead = Lead(**lead_doc)

        if lead.lead_status == LeadStatus.DO_NOT_CONTACT:
            raise ValidationError("Lead status is DO_NOT_CONTACT. Qualification is blocked.")
        if lead.lead_status == LeadStatus.INVALID:
            raise ValidationError("Lead status is INVALID. Qualification is blocked.")

        biz_id_str = str(lead.business_id)
        biz_doc = await self.business_repo.get_by_id(biz_id_str)
        if not biz_doc:
            raise NotFoundError(f"Associated business with ID '{biz_id_str}' not found.")
        biz_name = biz_doc.get("name", "Unknown Business")

        context_dict = await self.context_builder.build_context(lead_id)
        context_json = json.dumps(context_dict, indent=2)

        agent_run = await self.agent_run_service.create_run(
            AgentRun(
                agent_type=AgentType.LEAD_QUALIFICATION,
                status=AgentRunStatus.RUNNING,
                lead_id=self.lead_repo.parse_object_id(lead_id),
                business_id=self.business_repo.parse_object_id(biz_id_str),
                input_reference=f"lead_id={lead_id}",
            )
        )
        run_id = str(agent_run.id) if agent_run and agent_run.id else None

        system_msg = LLMMessage(role=LLMRole.SYSTEM, content=QUALIFICATION_SYSTEM_PROMPT)
        user_msg = LLMMessage(
            role=LLMRole.USER,
            content=QUALIFICATION_USER_PROMPT_TEMPLATE.format(context_json=context_json),
        )
        model_override = req.model if req else None

        try:
            llm_res = await self.llm_service.generate(
                LLMCompletionRequest(
                    messages=[system_msg, user_msg],
                    temperature=0.2,
                    task_type="lead_qualification",
                    model=model_override,
                )
            )

            qual_output, was_repaired = await self._parse_and_validate(
                llm_res.content, [system_msg, user_msg], model_override
            )

            primary_svc = (
                qual_output.recommended_services[0].service
                if qual_output.recommended_services
                else ServiceType.UNKNOWN
            )
            sec_svcs = [
                s.service for s in qual_output.recommended_services[1:] if s.service != ServiceType.UNKNOWN
            ]

            lead.qualification.qualification_score = qual_output.qualification_score
            lead.qualification.qualification_reason = qual_output.summary
            lead.score = qual_output.qualification_score
            lead.service_opportunity = ServiceOpportunity(
                primary_service=primary_svc,
                secondary_services=sec_svcs,
                opportunity_score=qual_output.qualification_score,
                reason=qual_output.summary,
            )

            existing_ev_types = {e.type for e in lead.evidence}
            for ev_str in qual_output.evidence:
                ev_enum = self._map_evidence_type(ev_str)
                if ev_enum and ev_enum not in existing_ev_types:
                    lead.evidence.append(
                        Evidence(
                            type=ev_enum,
                            description=f"AI Qualification signal: {ev_str}",
                            confidence=qual_output.confidence,
                        )
                    )
                    existing_ev_types.add(ev_enum)

            if lead.lead_status in (LeadStatus.NEW, LeadStatus.RESEARCHING):
                lead.lead_status = LeadStatus.QUALIFIED
            if lead.pipeline_stage in (PipelineStage.NEW, PipelineStage.RESEARCH):
                lead.pipeline_stage = PipelineStage.QUALIFIED

            update_dict = lead.model_dump(by_alias=True, exclude={"id"})
            await self.lead_repo.update_by_id(lead_id, update_dict)

            if run_id:
                await self.agent_run_service.run_repo.update_by_id(
                    run_id,
                    {
                        "status": AgentRunStatus.COMPLETED.value,
                        "output_data": {
                            "score": qual_output.qualification_score,
                            "label": qual_output.qualification_label.value,
                        },
                    },
                )

            return LeadQualificationResponse(
                lead_id=lead_id,
                business_id=biz_id_str,
                business_name=biz_name,
                qualification=qual_output,
                run_id=run_id,
            )

        except Exception as exc:
            logger.error(f"Qualification failed for lead {lead_id}: {exc}")
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
    ) -> tuple[QualificationLLMOutput, bool]:
        parsed = self._extract_json(raw_content)
        if parsed:
            try:
                out = QualificationLLMOutput.model_validate(parsed)
                return out, False
            except Exception as e:
                logger.warning(f"Initial LLM qualification validation failed: {e}")

        logger.info("Attempting single repair for LLM qualification output...")
        repair_msg = LLMMessage(role=LLMRole.USER, content=QUALIFICATION_REPAIR_PROMPT)
        repair_conv = conversation + [LLMMessage(role=LLMRole.ASSISTANT, content=raw_content), repair_msg]

        repair_res = await self.llm_service.generate(
            LLMCompletionRequest(
                messages=repair_conv,
                temperature=0.0,
                task_type="lead_qualification_repair",
                model=model_override,
            )
        )

        repaired_parsed = self._extract_json(repair_res.content)
        if repaired_parsed:
            try:
                out = QualificationLLMOutput.model_validate(repaired_parsed)
                return out, True
            except Exception as exc:
                logger.error(f"Repaired LLM qualification output validation failed: {exc}")

        raise ValidationError("Failed to produce structured JSON qualification result from LLM.")

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

    def _map_evidence_type(self, raw_str: str) -> Optional[EvidenceType]:
        s = raw_str.upper()
        for ev in EvidenceType:
            if ev.value in s:
                return ev
        return EvidenceType.OTHER
        self.context_builder = context_builder or LeadAIContextBuilder(
            lead_repo=self.lead_repo, business_repo=self.business_repo
        )
        self.ai_gen_service = ai_gen_service or AIGenerationService()
        self.llm_service = llm_service or LLMService(ai_generation_service=self.ai_gen_service)
        self.agent_run_service = agent_run_service or AgentRunService()
