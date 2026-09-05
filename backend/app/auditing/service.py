import logging
from typing import Optional
from app.auditing.checks import inspect_mobile_viewport, run_deterministic_website_audit
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.repositories.website_audit import WebsiteAuditRepository
from app.schemas.business import Business
from app.schemas.lead import Lead
from app.schemas.website_audit import WebsiteAudit
from app.verification.models import WebsiteFetchResult

logger = logging.getLogger(__name__)


class WebsiteAuditService:
    def __init__(
        self,
        audit_repo: Optional[WebsiteAuditRepository] = None,
        business_repo: Optional[BusinessRepository] = None,
        lead_repo: Optional[LeadRepository] = None,
    ):
        self.audit_repo = audit_repo or WebsiteAuditRepository()
        self.business_repo = business_repo or BusinessRepository()
        self.lead_repo = lead_repo or LeadRepository()

    async def perform_audit(
        self,
        business: Business,
        lead: Optional[Lead] = None,
        fetch_result: Optional[WebsiteFetchResult] = None,
    ) -> WebsiteAudit:
        """Perform lightweight deterministic website audit and save to MongoDB."""
        biz_id_str = str(business.id) if business.id else None
        lead_id_str = str(lead.id) if lead and lead.id else None

        website_url = business.website or (fetch_result.final_url if fetch_result else "")

        if not fetch_result:
            fetch_result = WebsiteFetchResult(accessible=False, error_message="No website available to audit.")

        overall_score, issues, strengths, recommendations = run_deterministic_website_audit(
            website_url=website_url,
            fetch_result=fetch_result,
        )

        mobile_friendly = inspect_mobile_viewport(fetch_result.html_content or "")

        biz_oid = self.audit_repo.parse_object_id(biz_id_str) if biz_id_str else None
        lead_oid = self.audit_repo.parse_object_id(lead_id_str) if lead_id_str else None

        audit_obj = WebsiteAudit(
            business_id=biz_oid,
            lead_id=lead_oid,
            website_url=website_url or "N/A",
            domain=business.normalized_domain,
            website_exists=fetch_result.accessible,
            http_status=fetch_result.status_code,
            https_enabled=fetch_result.final_url.startswith("https://") if fetch_result.final_url else False,
            mobile_friendly=mobile_friendly,
            performance_score=round(max(0.0, 100.0 - ((fetch_result.response_time_ms or 0.0) / 50.0)), 1),
            overall_score=overall_score,
            issues=issues,
            strengths=strengths,
            recommendations=recommendations,
            audit_version="1.0",
        )

        doc = audit_obj.model_dump(by_alias=True, exclude={"id"})
        created_doc = await self.audit_repo.create(doc)
        return WebsiteAudit(**created_doc)
