from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.api import (
    CampaignCreateRequest,
    CampaignUpdateRequest,
    PaginatedResponseEnvelope,
    SingleResponseEnvelope,
)
from app.schemas.campaign import Campaign
from app.services.campaign import CampaignService

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])


def get_campaign_service() -> CampaignService:
    return CampaignService()


@router.post("", response_model=SingleResponseEnvelope[Campaign], status_code=status.HTTP_201_CREATED)
async def create_campaign(
    req: CampaignCreateRequest,
    service: CampaignService = Depends(get_campaign_service),
):
    campaign = await service.create_campaign(req)
    return SingleResponseEnvelope(data=campaign)


@router.get("", response_model=PaginatedResponseEnvelope[Campaign])
async def list_campaigns(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: Optional[str] = Query(None),
    service: CampaignService = Depends(get_campaign_service),
):
    campaigns, meta = await service.list_campaigns(page=page, page_size=page_size, status=status)
    return PaginatedResponseEnvelope(data=campaigns, pagination=meta)


@router.get("/{campaign_id}", response_model=SingleResponseEnvelope[Campaign])
async def get_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
):
    campaign = await service.get_campaign(campaign_id)
    return SingleResponseEnvelope(data=campaign)


@router.patch("/{campaign_id}", response_model=SingleResponseEnvelope[Campaign])
async def update_campaign(
    campaign_id: str,
    req: CampaignUpdateRequest,
    service: CampaignService = Depends(get_campaign_service),
):
    campaign = await service.update_campaign(campaign_id, req)
    return SingleResponseEnvelope(data=campaign)
