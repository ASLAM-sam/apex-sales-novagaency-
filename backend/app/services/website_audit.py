from typing import List, Optional
from app.core.exceptions import NotFoundError
from app.repositories.business import BusinessRepository
from app.repositories.lead import LeadRepository
from app.repositories.website_audit import WebsiteAuditRepository
from app.schemas.api import WebsiteAuditCreateRequest
from app.schemas.website_audit import WebsiteAudit


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

    async def create_audit(self, req: WebsiteAuditCreateRequest) -> WebsiteAudit:
        biz_doc = await self.business_repo.get_by_id(req.business_id)
        if not biz_doc:
            raise NotFoundError(f"Business with ID '{req.business_id}' not found.")

        lead_oid = None
        if req.lead_id:
            lead_doc = await self.lead_repo.get_by_id(req.lead_id)
            if not lead_doc:
                raise NotFoundError(f"Lead with ID '{req.lead_id}' not found.")
            lead_oid = self.audit_repo.parse_object_id(req.lead_id)

        audit_obj = WebsiteAudit(
            business_id=self.audit_repo.parse_object_id(req.business_id),
            lead_id=lead_oid,
            website_url=req.website_url,
            domain=req.domain,
            website_exists=req.website_exists,
            http_status=req.http_status,
            https_enabled=req.https_enabled,
            mobile_friendly=req.mobile_friendly,
            performance_score=req.performance_score,
            seo_score=req.seo_score,
            accessibility_score=req.accessibility_score,
            design_score=req.design_score,
            content_score=req.content_score,
            conversion_score=req.conversion_score,
            overall_score=req.overall_score,
            issues=req.issues,
            strengths=req.strengths,
            recommendations=req.recommendations,
        )

        doc = audit_obj.model_dump(by_alias=True, exclude={"id"})
        created_doc = await self.audit_repo.create(doc)
        return WebsiteAudit(**created_doc)

    async def get_audit(self, audit_id: str) -> WebsiteAudit:
        doc = await self.audit_repo.get_by_id(audit_id)
        if not doc:
            raise NotFoundError(f"Website audit record with ID '{audit_id}' not found.")
        return WebsiteAudit(**doc)

    async def get_audits_by_business(self, business_id: str) -> List[WebsiteAudit]:
        await self.business_repo.get_by_id(business_id)
        items = await self.audit_repo.get_by_business_id(business_id)
        return [WebsiteAudit(**d) for d in items]
