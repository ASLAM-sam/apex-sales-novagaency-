from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import utc_now
from app.schemas.enums import OutreachChannel, OutreachMessageType, OutreachStatus, ServiceType


class PitchLLMOutput(BaseModel):
    channel: OutreachChannel = OutreachChannel.EMAIL
    message_type: OutreachMessageType = OutreachMessageType.INITIAL_PITCH
    subject: Optional[str] = None
    body: str
    personalization_points: List[str] = Field(default_factory=list)
    evidence_used: List[str] = Field(default_factory=list)
    recommended_service: ServiceType = ServiceType.UNKNOWN
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)


class PitchGenerationRequest(BaseModel):
    channel: OutreachChannel = OutreachChannel.EMAIL
    message_type: OutreachMessageType = OutreachMessageType.INITIAL_PITCH
    model: Optional[str] = None
    force_refresh: bool = False


class PitchGenerationResponse(BaseModel):
    lead_id: str
    business_id: str
    outreach_id: str
    channel: OutreachChannel
    message_type: OutreachMessageType
    subject: Optional[str] = None
    body: str
    personalization_points: List[str] = Field(default_factory=list)
    evidence_used: List[str] = Field(default_factory=list)
    recommended_service: ServiceType = ServiceType.UNKNOWN
    confidence: float
    status: OutreachStatus = OutreachStatus.DRAFT
    run_id: Optional[str] = None
    ai_generation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
