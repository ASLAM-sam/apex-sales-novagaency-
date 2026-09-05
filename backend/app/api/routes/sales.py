import logging
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from app.sales.schemas import (
    LeadTimelineResponse,
    SalesActionRequest,
    SalesActionResponse,
    SalesLeadDetailResponse,
    SalesLeadListResponse,
)
from app.sales.service import SalesWorkspaceService
from app.schemas.enums import OutreachChannel

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/sales", tags=["Sales Workspace Pipeline & Actions"])


def get_sales_workspace_service() -> SalesWorkspaceService:
    return SalesWorkspaceService()


@router.get(
    "/leads",
    response_model=SalesLeadListResponse,
    status_code=status.HTTP_200_OK,
    summary="List Filtered Sales Leads Pipeline",
    description=(
        "Retrieves a paginated list of enriched sales leads supporting filters for status, stage, "
        "score range, service type, location, category, verification, audit/pitch availability, "
        "and safe sorting."
    ),
)
async def list_sales_leads(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    lead_status: Optional[str] = Query(default=None),
    pipeline_stage: Optional[str] = Query(default=None),
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    max_score: Optional[float] = Query(default=None, ge=0, le=100),
    service_type: Optional[str] = Query(default=None),
    city: Optional[str] = Query(default=None),
    category: Optional[str] = Query(default=None),
    lead_source: Optional[str] = Query(default=None),
    verification_status: Optional[str] = Query(default=None),
    has_website: Optional[bool] = Query(default=None),
    has_audit: Optional[bool] = Query(default=None),
    has_pitch: Optional[bool] = Query(default=None),
    sort_by: str = Query(default="created_at"),
    sort_order: str = Query(default="desc"),
    service: SalesWorkspaceService = Depends(get_sales_workspace_service),
) -> SalesLeadListResponse:
    return await service.list_sales_leads(
        page=page,
        page_size=page_size,
        lead_status=lead_status,
        pipeline_stage=pipeline_stage,
        min_score=min_score,
        max_score=max_score,
        service_type=service_type,
        city=city,
        category=category,
        lead_source=lead_source,
        verification_status=verification_status,
        has_website=has_website,
        has_audit=has_audit,
        has_pitch=has_pitch,
        sort_by=sort_by,
        sort_order=sort_order,
    )


@router.get(
    "/leads/{lead_id}",
    response_model=SalesLeadDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Unified Lead Detail Sales View",
    description=(
        "Composes a unified read-model view of a lead, including business details, verification, "
        "latest research, website audit, qualification, outreach history, readiness flags, "
        "next recommended action, and prepared contact action data."
    ),
)
async def get_lead_detail(
    lead_id: str,
    service: SalesWorkspaceService = Depends(get_sales_workspace_service),
) -> SalesLeadDetailResponse:
    return await service.get_lead_detail(lead_id)


@router.get(
    "/leads/{lead_id}/timeline",
    response_model=LeadTimelineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Lead Activity Timeline",
    description="Returns a lightweight chronological activity timeline composed from existing domain records.",
)
async def get_lead_timeline(
    lead_id: str,
    service: SalesWorkspaceService = Depends(get_sales_workspace_service),
) -> LeadTimelineResponse:
    return await service.get_lead_timeline(lead_id)


@router.post(
    "/leads/{lead_id}/prepare",
    status_code=status.HTTP_200_OK,
    summary="Inspect Action Readiness & Recommended Next Action",
    description="Analyzes lead state and returns frontend-ready action readiness flags and recommended next step.",
)
async def prepare_lead(
    lead_id: str,
    service: SalesWorkspaceService = Depends(get_sales_workspace_service),
) -> Dict[str, Any]:
    return await service.prepare_lead(lead_id)


@router.post(
    "/leads/{lead_id}/actions/{action_type}",
    response_model=SalesActionResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger Explicit Sales Action",
    description=(
        "Triggers explicit sales actions: RUN_INTELLIGENCE, QUALIFY, or GENERATE_PITCH. "
        "Does NOT allow arbitrary execution or direct transition to SENT."
    ),
)
async def execute_sales_action(
    lead_id: str,
    action_type: str,
    payload: Optional[SalesActionRequest] = None,
    service: SalesWorkspaceService = Depends(get_sales_workspace_service),
) -> SalesActionResponse:
    req = payload or SalesActionRequest()
    return await service.execute_sales_action(
        lead_id=lead_id,
        action_type=action_type,
        force_refresh=req.force_refresh,
        channel=req.channel or OutreachChannel.EMAIL,
    )
