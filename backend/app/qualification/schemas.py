from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import MongoBaseModel, utc_now
from app.schemas.enums import ServiceType


class OpportunityLabel(str, Enum):
    LOW_OPPORTUNITY = "LOW_OPPORTUNITY"
    POSSIBLE = "POSSIBLE"
    GOOD = "GOOD"
    HIGH = "HIGH"
    VERY_HIGH = "VERY_HIGH"
    INSUFFICIENT_DATA = "INSUFFICIENT_DATA"
    INVALID = "INVALID"


class ServiceOpportunityDetail(BaseModel):
    service: ServiceType = ServiceType.UNKNOWN
    reason: str
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    evidence: List[str] = Field(default_factory=list)


class QualificationLLMOutput(BaseModel):
    qualification_score: float = Field(ge=0.0, le=100.0)
    qualification_label: OpportunityLabel
    confidence: float = Field(ge=0.0, le=1.0)
    recommended_services: List[ServiceOpportunityDetail] = Field(default_factory=list)
    reasons: List[str] = Field(default_factory=list)
    positive_signals: List[str] = Field(default_factory=list)
    negative_signals: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    summary: str


class LeadQualificationRequest(BaseModel):
    force_refresh: bool = False
    model: Optional[str] = None


class LeadQualificationResponse(BaseModel):
    lead_id: str
    business_id: str
    business_name: str
    qualification: QualificationLLMOutput
    run_id: Optional[str] = None
    ai_generation_id: Optional[str] = None
    created_at: datetime = Field(default_factory=utc_now)
