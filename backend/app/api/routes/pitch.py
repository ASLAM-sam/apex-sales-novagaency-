import logging
from typing import Optional
from fastapi import APIRouter, status
from app.pitch.schemas import PitchGenerationRequest, PitchGenerationResponse
from app.pitch.service import PitchGenerationService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/leads/{lead_id}/pitch",
    response_model=PitchGenerationResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate AI Personalized Outreach Pitch Draft",
    description=(
        "Generates a personalized, evidence-grounded pitch draft (EMAIL, WHATSAPP, MANUAL) "
        "and saves it as an Outreach DRAFT record. Messages are NEVER automatically sent."
    ),
)
async def generate_pitch(
    lead_id: str,
    payload: Optional[PitchGenerationRequest] = None,
) -> PitchGenerationResponse:
    service = PitchGenerationService()
    return await service.generate_pitch(lead_id=lead_id, req=payload)
