import logging
from typing import Optional
from app.auditing.service import WebsiteAuditService
from app.core.exceptions import NotFoundError
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.research.service import ResearchService
from app.schemas.agent_run import AgentRun
from app.schemas.business import Business
from app.schemas.enums import AgentRunStatus, AgentType, IssueSeverity
from app.schemas.intelligence import (
    LeadIntelligenceRequest,
    LeadIntelligenceResponse,
    VerificationSummary,
    WebsiteAuditSummary,
)
from app.schemas.lead import Lead
from app.services.agent_run import AgentRunService
from app.verification.service import VerificationService

logger = logging.getLogger(__name__)


class LeadIntelligenceService:
    def __init__(
        self,
        lead_repo: Optional[LeadRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
        verification_service: Optional[VerificationService] = None,
        research_service: Optional[ResearchService] = None,
        audit_service: Optional[WebsiteAuditService] = None,
        agent_run_service: Optional[AgentRunService] = None,
    ):
        self.lead_repo = lead_repo or LeadRepository()
        self.business_repo = business_repo or BusinessRepository()
        self.verification_service = verification_service or VerificationService(business_repo=self.business_repo)
        self.research_service = research_service or ResearchService(
            business_repo=self.business_repo, lead_repo=self.lead_repo
        )
        self.audit_service = audit_service or WebsiteAuditService(
            business_repo=self.business_repo, lead_repo=self.lead_repo
        )
        self.agent_run_service = agent_run_service or AgentRunService()

    async def process_lead_intelligence(
        self, lead_id: str, req: Optional[LeadIntelligenceRequest] = None
    ) -> LeadIntelligenceResponse:
        lead_doc = await self.lead_repo.get_by_id(lead_id)
        if not lead_doc:
            raise NotFoundError(f"Lead with ID '{lead_id}' not found.")
        lead = Lead(**lead_doc)

        biz_id_str = str(lead.business_id)
        biz_doc = await self.business_repo.get_by_id(biz_id_str)
        if not biz_doc:
            raise NotFoundError(f"Associated business with ID '{biz_id_str}' not found.")
        business = Business(**biz_doc)

        agent_run = await self.agent_run_service.create_run(
            AgentRun(
                agent_type=AgentType.LEAD_VERIFICATION,
                status=AgentRunStatus.RUNNING,
                lead_id=self.lead_repo.parse_object_id(lead_id),
                business_id=self.business_repo.parse_object_id(biz_id_str),
                input_reference=f"lead_id={lead_id}, business_id={biz_id_str}",
            )
        )
        run_id = str(agent_run.id) if agent_run and agent_run.id else None

        # Step 1: Verification
        verification_res, fetch_res = await self.verification_service.verify_business(business)

        # Step 2: Research (Isolated Failure Protection)
        research_rec = None
        try:
            research_rec = await self.research_service.perform_research(
                business=business, lead=lead, fetch_result=fetch_res
            )
        except Exception as e:
            logger.error(f"Research error for lead {lead_id}: {e}")

        # Step 3: Website Audit (Isolated Failure Protection)
        audit_rec = None
        try:
            audit_rec = await self.audit_service.perform_audit(
                business=business, lead=lead, fetch_result=fetch_res
            )
        except Exception as e:
            logger.error(f"Website audit error for lead {lead_id}: {e}")

        if run_id:
            try:
                await self.agent_run_service.run_repo.update_by_id(
                    run_id,
                    {
                        "status": AgentRunStatus.COMPLETED.value,
                        "output_data": {
                            "verification_status": verification_res.verification_status.value,
                            "audit_score": audit_rec.overall_score if audit_rec else None,
                        },
                    },
                )
            except Exception as e:
                logger.error(f"Failed to update agent run {run_id}: {e}")

        v_summary = VerificationSummary(
            verification_status=verification_res.verification_status,
            business_exists_evidence=verification_res.business_exists_evidence,
            website_accessible=verification_res.website_accessible,
            domain_matches=verification_res.domain_matches,
            business_name_found=verification_res.business_name_found,
            phone_present=verification_res.phone_present,
            email_present=verification_res.email_present,
            notes=verification_res.notes,
        )

        audit_summary = None
        if audit_rec:
            high_crit = sum(1 for i in audit_rec.issues if i.severity in (IssueSeverity.HIGH, IssueSeverity.CRITICAL))
            top_rec = audit_rec.recommendations[0] if audit_rec.recommendations else None
            audit_summary = WebsiteAuditSummary(
                audit_id=str(audit_rec.id) if audit_rec.id else None,
                website_exists=audit_rec.website_exists,
                http_status=audit_rec.http_status,
                overall_score=audit_rec.overall_score,
                total_issues=len(audit_rec.issues),
                high_critical_issues=high_crit,
                top_recommendation=top_rec,
            )

        return LeadIntelligenceResponse(
            lead_id=lead_id,
            business_id=biz_id_str,
            business_name=business.name,
            processing_status="COMPLETED",
            verification=v_summary,
            research=research_rec,
            website_audit=audit_summary,
            run_id=run_id,
        )
