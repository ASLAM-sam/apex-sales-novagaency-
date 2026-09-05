import logging
from typing import Optional
from fastapi import APIRouter, status
from app.intelligence.service import LeadIntelligenceService
from app.schemas.intelligence import LeadIntelligenceRequest, LeadIntelligenceResponse

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(
    "/leads/{lead_id}/intelligence",
    response_model=LeadIntelligenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Run Lead Intelligence (Verification + Research + Website Audit)",
    description=(
        "Executes verification, deterministic research, and lightweight website health auditing "
        "for a given lead and stores output in MongoDB without sending outreach or running AI models."
    ),
)
async def run_lead_intelligence(
    lead_id: str,
    payload: Optional[LeadIntelligenceRequest] = None,
) -> LeadIntelligenceResponse:
    service = LeadIntelligenceService()
    return await service.process_lead_intelligence(lead_id=lead_id, req=payload)
