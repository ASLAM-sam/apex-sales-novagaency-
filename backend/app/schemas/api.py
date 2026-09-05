from datetime import datetime
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from app.schemas.enums import (
    BusinessStatus,
    CampaignStatus,
    ConversationIntent,
    ConversationStatus,
    LeadSource,
    LeadStatus,
    OutreachChannel,
    OutreachDirection,
    OutreachMessageType,
    OutreachStatus,
    PipelineStage,
    ServiceType,
    VerificationStatus,
)
from app.schemas.business import SocialProfiles, SourceRecord
from app.schemas.lead import Contact, Evidence, Qualification, ServiceOpportunity, SourceReference
from app.schemas.research import ResearchSource
from app.schemas.website_audit import AuditIssue

T = TypeVar("T")


class PaginationMetadata(BaseModel):
    page: int
    page_size: int
    total: int
    pages: int


class SingleResponseEnvelope(BaseModel, Generic[T]):
    data: T


class PaginatedResponseEnvelope(BaseModel, Generic[T]):
    data: List[T]
    pagination: PaginationMetadata


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponseEnvelope(BaseModel):
    error: ErrorDetail


# API Request Models

class BusinessCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    social_profiles: Optional[SocialProfiles] = None
    source_records: List[SourceRecord] = Field(default_factory=list)
    business_status: BusinessStatus = BusinessStatus.UNKNOWN
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED


class BusinessUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    sub_category: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    social_profiles: Optional[SocialProfiles] = None
    business_status: Optional[BusinessStatus] = None
    verification_status: Optional[VerificationStatus] = None


class LeadCreateRequest(BaseModel):
    business_id: str
    contact: Optional[Contact] = None
    lead_source: LeadSource = LeadSource.MANUAL
    source_reference: Optional[SourceReference] = None
    lead_status: LeadStatus = LeadStatus.NEW
    pipeline_stage: PipelineStage = PipelineStage.NEW
    qualification: Optional[Qualification] = None
    score: Optional[float] = None
    service_opportunity: Optional[ServiceOpportunity] = None
    evidence: List[Evidence] = Field(default_factory=list)
    next_follow_up_at: Optional[datetime] = None
    assigned_to: Optional[str] = None


class LeadUpdateRequest(BaseModel):
    contact: Optional[Contact] = None
    lead_source: Optional[LeadSource] = None
    lead_status: Optional[LeadStatus] = None
    pipeline_stage: Optional[PipelineStage] = None
    qualification: Optional[Qualification] = None
    score: Optional[float] = None
    service_opportunity: Optional[ServiceOpportunity] = None
    evidence: Optional[List[Evidence]] = None
    next_follow_up_at: Optional[datetime] = None


class ResearchCreateRequest(BaseModel):
    business_id: str
    lead_id: Optional[str] = None
    business_summary: Optional[str] = None
    products_services: List[str] = Field(default_factory=list)
    target_audience: Optional[str] = None
    location_summary: Optional[str] = None
    online_presence: Optional[str] = None
    social_presence: Optional[str] = None
    competitive_context: Optional[str] = None
    business_signals: List[str] = Field(default_factory=list)
    research_sources: List[ResearchSource] = Field(default_factory=list)
    research_confidence: Optional[float] = None
    research_version: str = "1.0"


class WebsiteAuditCreateRequest(BaseModel):
    business_id: str
    lead_id: Optional[str] = None
    website_url: str
    domain: Optional[str] = None
    website_exists: bool = True
    http_status: Optional[int] = None
    https_enabled: Optional[bool] = None
    mobile_friendly: Optional[bool] = None
    performance_score: Optional[float] = None
    seo_score: Optional[float] = None
    accessibility_score: Optional[float] = None
    design_score: Optional[float] = None
    content_score: Optional[float] = None
    conversion_score: Optional[float] = None
    overall_score: Optional[float] = None
    issues: List[AuditIssue] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)


class OutreachCreateRequest(BaseModel):
    lead_id: str
    business_id: str
    channel: OutreachChannel
    direction: OutreachDirection = OutreachDirection.OUTBOUND
    message_type: OutreachMessageType = OutreachMessageType.INITIAL_PITCH
    subject: Optional[str] = None
    message: str
    status: OutreachStatus = OutreachStatus.DRAFT


class OutreachUpdateRequest(BaseModel):
    subject: Optional[str] = None
    message: Optional[str] = None
    status: Optional[OutreachStatus] = None


class ConversationCreateRequest(BaseModel):
    lead_id: str
    business_id: str
    channel: OutreachChannel
    status: ConversationStatus = ConversationStatus.OPEN
    sentiment: Optional[str] = None
    intent: ConversationIntent = ConversationIntent.UNKNOWN
    ai_summary: Optional[str] = None
    next_action: Optional[str] = None
    next_follow_up_at: Optional[datetime] = None


class ConversationUpdateRequest(BaseModel):
    status: Optional[ConversationStatus] = None
    sentiment: Optional[str] = None
    intent: Optional[ConversationIntent] = None
    ai_summary: Optional[str] = None
    next_action: Optional[str] = None
    next_follow_up_at: Optional[datetime] = None


class CampaignCreateRequest(BaseModel):
    name: str
    description: Optional[str] = None
    status: CampaignStatus = CampaignStatus.DRAFT
    target_service: Optional[ServiceType] = None
    target_industry: Optional[str] = None
    lead_filters: Dict[str, Any] = Field(default_factory=dict)


class CampaignUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[CampaignStatus] = None
    target_service: Optional[ServiceType] = None
    target_industry: Optional[str] = None
    lead_filters: Optional[Dict[str, Any]] = None

    assigned_to: Optional[str] = None
