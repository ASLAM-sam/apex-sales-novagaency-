from datetime import datetime
from typing import List, Optional
from pydantic import AliasChoices, Field, field_validator
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now, validate_score_range
from app.schemas.enums import EvidenceType, LeadSource, LeadStatus, PipelineStage, ServiceType


class Contact(MongoBaseModel):
    name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    whatsapp: Optional[str] = None
    linkedin: Optional[str] = None


class SourceReference(MongoBaseModel):
    source_url: Optional[str] = None
    source_id: Optional[str] = None
    discovered_at: datetime = Field(default_factory=utc_now)


class Qualification(MongoBaseModel):
    is_genuine_business: Optional[bool] = None
    has_contact_method: Optional[bool] = None
    website_quality: Optional[float] = None
    website_need: Optional[float] = None
    service_fit: Optional[float] = None
    buying_signal: Optional[float] = None
    qualification_score: Optional[float] = None
    qualification_reason: Optional[str] = None

    @field_validator(
        "website_quality",
        "website_need",
        "service_fit",
        "buying_signal",
        "qualification_score",
        mode="before",
    )
    @classmethod
    def check_score(cls, v: Optional[float]) -> Optional[float]:
        return validate_score_range(v)


class ServiceOpportunity(MongoBaseModel):
    primary_service: ServiceType = ServiceType.UNKNOWN
    secondary_services: List[ServiceType] = Field(default_factory=list)
    opportunity_score: Optional[float] = None
    reason: Optional[str] = None

    @field_validator("opportunity_score", mode="before")
    @classmethod
    def check_score(cls, v: Optional[float]) -> Optional[float]:
        return validate_score_range(v)


class Evidence(MongoBaseModel):
    type: EvidenceType
    description: str
    source_url: Optional[str] = None
    observed_at: datetime = Field(default_factory=utc_now)
    confidence: Optional[float] = None

    @field_validator("confidence", mode="before")
    @classmethod
    def check_score(cls, v: Optional[float]) -> Optional[float]:
        return validate_score_range(v)


class Lead(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")
    business_id: PyObjectId

    contact: Contact = Field(default_factory=Contact)
    lead_source: LeadSource = LeadSource.MANUAL
    source_reference: Optional[SourceReference] = None

    lead_status: LeadStatus = LeadStatus.NEW
    pipeline_stage: PipelineStage = PipelineStage.NEW

    qualification: Qualification = Field(default_factory=Qualification)
    score: Optional[float] = None
    service_opportunity: Optional[ServiceOpportunity] = None
    evidence: List[Evidence] = Field(default_factory=list)

    last_contacted_at: Optional[datetime] = None
    next_follow_up_at: Optional[datetime] = None
    assigned_to: Optional[str] = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("score", mode="before")
    @classmethod
    def check_score(cls, v: Optional[float]) -> Optional[float]:
        return validate_score_range(v)
