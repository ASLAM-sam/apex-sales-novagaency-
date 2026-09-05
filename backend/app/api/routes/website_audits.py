from typing import List
from fastapi import APIRouter, Depends, status
from app.schemas.api import SingleResponseEnvelope, WebsiteAuditCreateRequest
from app.schemas.website_audit import WebsiteAudit
from app.services.website_audit import WebsiteAuditService

router = APIRouter(tags=["Website Audits"])


def get_audit_service() -> WebsiteAuditService:
    return WebsiteAuditService()


@router.post("/website-audits", response_model=SingleResponseEnvelope[WebsiteAudit], status_code=status.HTTP_201_CREATED)
async def create_audit(
    req: WebsiteAuditCreateRequest,
    service: WebsiteAuditService = Depends(get_audit_service),
):
    audit = await service.create_audit(req)
    return SingleResponseEnvelope(data=audit)


@router.get("/website-audits/{audit_id}", response_model=SingleResponseEnvelope[WebsiteAudit])
async def get_audit(
    audit_id: str,
    service: WebsiteAuditService = Depends(get_audit_service),
):
    audit = await service.get_audit(audit_id)
    return SingleResponseEnvelope(data=audit)


@router.get("/businesses/{business_id}/website-audits", response_model=SingleResponseEnvelope[List[WebsiteAudit]])
async def get_audits_by_business(
    business_id: str,
    service: WebsiteAuditService = Depends(get_audit_service),
):
    audits = await service.get_audits_by_business(business_id)
    return SingleResponseEnvelope(data=audits)
