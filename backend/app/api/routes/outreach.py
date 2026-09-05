from typing import List
from fastapi import APIRouter, Depends, status
from app.schemas.api import OutreachCreateRequest, OutreachUpdateRequest, SingleResponseEnvelope
from app.schemas.outreach import Outreach
from app.services.outreach import OutreachService

router = APIRouter(tags=["Outreach"])


def get_outreach_service() -> OutreachService:
    return OutreachService()


@router.post("/outreach", response_model=SingleResponseEnvelope[Outreach], status_code=status.HTTP_201_CREATED)
async def create_outreach(
    req: OutreachCreateRequest,
    service: OutreachService = Depends(get_outreach_service),
):
    outreach = await service.create_outreach(req)
    return SingleResponseEnvelope(data=outreach)


@router.get("/outreach/{outreach_id}", response_model=SingleResponseEnvelope[Outreach])
async def get_outreach(
    outreach_id: str,
    service: OutreachService = Depends(get_outreach_service),
):
    outreach = await service.get_outreach(outreach_id)
    return SingleResponseEnvelope(data=outreach)


@router.get("/leads/{lead_id}/outreach", response_model=SingleResponseEnvelope[List[Outreach]])
async def get_outreach_for_lead(
    lead_id: str,
    service: OutreachService = Depends(get_outreach_service),
):
    items = await service.list_outreach_for_lead(lead_id)
    return SingleResponseEnvelope(data=items)


@router.patch("/outreach/{outreach_id}", response_model=SingleResponseEnvelope[Outreach])
async def update_outreach(
    outreach_id: str,
    req: OutreachUpdateRequest,
    service: OutreachService = Depends(get_outreach_service),
):
    outreach = await service.update_outreach(outreach_id, req)
    return SingleResponseEnvelope(data=outreach)
