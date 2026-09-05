from typing import List
from fastapi import APIRouter, Depends, status
from app.schemas.api import ResearchCreateRequest, SingleResponseEnvelope
from app.schemas.research import Research
from app.services.research import ResearchService

router = APIRouter(tags=["Research"])


def get_research_service() -> ResearchService:
    return ResearchService()


@router.post("/research", response_model=SingleResponseEnvelope[Research], status_code=status.HTTP_201_CREATED)
async def create_research(
    req: ResearchCreateRequest,
    service: ResearchService = Depends(get_research_service),
):
    research = await service.create_research(req)
    return SingleResponseEnvelope(data=research)


@router.get("/research/{research_id}", response_model=SingleResponseEnvelope[Research])
async def get_research(
    research_id: str,
    service: ResearchService = Depends(get_research_service),
):
    research = await service.get_research(research_id)
    return SingleResponseEnvelope(data=research)


@router.get("/businesses/{business_id}/research", response_model=SingleResponseEnvelope[List[Research]])
async def get_research_by_business(
    business_id: str,
    service: ResearchService = Depends(get_research_service),
):
    research_list = await service.get_research_by_business(business_id)
    return SingleResponseEnvelope(data=research_list)
