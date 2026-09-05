from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.api import (
    LeadCreateRequest,
    LeadUpdateRequest,
    PaginatedResponseEnvelope,
    SingleResponseEnvelope,
)
from app.schemas.lead import Lead
from app.services.lead import LeadService

router = APIRouter(prefix="/leads", tags=["Leads"])


def get_lead_service() -> LeadService:
    return LeadService()


@router.post("", response_model=SingleResponseEnvelope[Lead], status_code=status.HTTP_201_CREATED)
async def create_lead(
    req: LeadCreateRequest,
    service: LeadService = Depends(get_lead_service),
):
    lead = await service.create_lead(req)
    return SingleResponseEnvelope(data=lead)


@router.get("", response_model=PaginatedResponseEnvelope[Lead])
async def list_leads(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    lead_status: Optional[str] = Query(None),
    pipeline_stage: Optional[str] = Query(None),
    lead_source: Optional[str] = Query(None),
    business_id: Optional[str] = Query(None),
    min_score: Optional[float] = Query(None, ge=0, le=100),
    max_score: Optional[float] = Query(None, ge=0, le=100),
    service: LeadService = Depends(get_lead_service),
):
    leads, meta = await service.list_leads(
        page=page,
        page_size=page_size,
        lead_status=lead_status,
        pipeline_stage=pipeline_stage,
        lead_source=lead_source,
        business_id=business_id,
        min_score=min_score,
        max_score=max_score,
    )
    return PaginatedResponseEnvelope(data=leads, pagination=meta)


@router.get("/{lead_id}", response_model=SingleResponseEnvelope[Lead])
async def get_lead(
    lead_id: str,
    service: LeadService = Depends(get_lead_service),
):
    lead = await service.get_lead(lead_id)
    return SingleResponseEnvelope(data=lead)


@router.patch("/{lead_id}", response_model=SingleResponseEnvelope[Lead])
async def update_lead(
    lead_id: str,
    req: LeadUpdateRequest,
    service: LeadService = Depends(get_lead_service),
):
    lead = await service.update_lead(lead_id, req)
    return SingleResponseEnvelope(data=lead)
