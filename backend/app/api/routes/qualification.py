import logging
from typing import Optional
from fastapi import APIRouter, status
from app.qualification.schemas import LeadQualificationRequest, LeadQualificationResponse
from app.qualification.service import LeadQualificationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/leads/{lead_id}/qualify",
    response_model=LeadQualificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Qualify Lead using AI Reasoning over Business Evidence",
    description=(
        "Performs evidence-grounded AI lead qualification over stored verification, research, "
        "and website audit signals using OmniRoute and LLMService. Updates lead score and qualification fields."
    ),
)
async def qualify_lead(
    lead_id: str,
    payload: Optional[LeadQualificationRequest] = None,
) -> LeadQualificationResponse:
    service = LeadQualificationService()
    return await service.qualify_lead(lead_id=lead_id, req=payload)
