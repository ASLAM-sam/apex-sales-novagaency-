from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.schemas.api import (
    BusinessCreateRequest,
    BusinessUpdateRequest,
    PaginatedResponseEnvelope,
    SingleResponseEnvelope,
)
from app.schemas.business import Business
from app.services.business import BusinessService

router = APIRouter(prefix="/businesses", tags=["Businesses"])


def get_business_service() -> BusinessService:
    return BusinessService()


@router.post("", response_model=SingleResponseEnvelope[Business], status_code=status.HTTP_201_CREATED)
async def create_business(
    req: BusinessCreateRequest,
    service: BusinessService = Depends(get_business_service),
):
    biz = await service.create_business(req)
    return SingleResponseEnvelope(data=biz)


@router.get("", response_model=PaginatedResponseEnvelope[Business])
async def list_businesses(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    search: Optional[str] = Query(None),
    city: Optional[str] = Query(None),
    state: Optional[str] = Query(None),
    country: Optional[str] = Query(None),
    verification_status: Optional[str] = Query(None),
    business_status: Optional[str] = Query(None),
    service: BusinessService = Depends(get_business_service),
):
    businesses, meta = await service.list_businesses(
        page=page,
        page_size=page_size,
        search=search,
        city=city,
        state=state,
        country=country,
        verification_status=verification_status,
        business_status=business_status,
    )
    return PaginatedResponseEnvelope(data=businesses, pagination=meta)


@router.get("/{business_id}", response_model=SingleResponseEnvelope[Business])
async def get_business(
    business_id: str,
    service: BusinessService = Depends(get_business_service),
):
    biz = await service.get_business(business_id)
    return SingleResponseEnvelope(data=biz)


@router.patch("/{business_id}", response_model=SingleResponseEnvelope[Business])
async def update_business(
    business_id: str,
    req: BusinessUpdateRequest,
    service: BusinessService = Depends(get_business_service),
):
    biz = await service.update_business(business_id, req)
    return SingleResponseEnvelope(data=biz)
