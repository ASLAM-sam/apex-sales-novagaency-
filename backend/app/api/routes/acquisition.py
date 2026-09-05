import logging
from typing import Optional
from fastapi import APIRouter, Depends, status
from app.acquisition.schemas import (
    AcquisitionImportRequest,
    AcquisitionImportResponse,
    AcquisitionSearchRequest,
    AcquisitionSearchResponse,
)
from app.acquisition.service import LeadAcquisitionService

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/acquisition", tags=["Lead Acquisition Workflow"])


def get_acquisition_service() -> LeadAcquisitionService:
    return LeadAcquisitionService()


@router.post(
    "/search",
    response_model=AcquisitionSearchResponse,
    status_code=status.HTTP_200_OK,
    summary="Search Candidate Businesses",
    description=(
        "Performs a provider-independent candidate business search using registered sources. "
        "Normalizes output, checks existing MongoDB businesses/leads, and returns candidate models. "
        "Does NOT automatically save candidates or send external communications."
    ),
)
async def search_candidates(
    payload: Optional[AcquisitionSearchRequest] = None,
    service: LeadAcquisitionService = Depends(get_acquisition_service),
) -> AcquisitionSearchResponse:
    req = payload or AcquisitionSearchRequest()
    return await service.search(req)


@router.post(
    "/import",
    response_model=AcquisitionImportResponse,
    status_code=status.HTTP_200_OK,
    summary="Import Candidate Businesses",
    description=(
        "Imports selected candidate business records. Checks existing businesses and leads, "
        "prevents duplicates using Phase 6 deduplication rules, respects DO_NOT_CONTACT states, "
        "and creates Business/Lead records as appropriate."
    ),
)
async def import_candidates(
    payload: AcquisitionImportRequest,
    service: LeadAcquisitionService = Depends(get_acquisition_service),
) -> AcquisitionImportResponse:
    return await service.import_candidates(payload)
