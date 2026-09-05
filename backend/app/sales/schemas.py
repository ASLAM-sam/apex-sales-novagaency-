from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.api import PaginationMetadata
from app.schemas.business import Business
from app.schemas.enums import OutreachChannel
from app.schemas.lead import Lead, Qualification
from app.schemas.outreach import Outreach


class DashboardSummaryResponse(BaseModel):
    total_businesses: int = 0
    total_leads: int = 0
    new_leads: int = 0
    qualified_leads: int = 0
    high_opportunity_leads: int = 0
    contacted_leads: int = 0
    replied_leads: int = 0
    interested_leads: int = 0
    follow_up_leads: int = 0
    converted_leads: int = 0
    lost_leads: int = 0
    draft_outreach_count: int = 0


class SalesLeadSummary(BaseModel):
    lead_id: str
    business_id: str
    business_name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    category: Optional[str] = None
    lead_status: str
    pipeline_stage: str
    qualification_score: Optional[float] = None
    qualification_status: Optional[str] = None
    primary_service: Optional[str] = None
    verification_status: Optional[str] = None
    has_website: bool = False
    has_audit: bool = False
    has_pitch: bool = False
    created_at: datetime
    next_follow_up_at: Optional[datetime] = None


class SalesLeadListResponse(BaseModel):
    leads: List[SalesLeadSummary]
    pagination: PaginationMetadata


class ReadinessFlags(BaseModel):
    can_verify: bool = True
    can_research: bool = True
    can_audit: bool = False
    can_qualify: bool = True
    can_generate_pitch: bool = True
    has_email: bool = False
    has_phone: bool = False
    has_website: bool = False
    has_draft: bool = False
    is_do_not_contact: bool = False


class ContactActionData(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    whatsapp_available: bool = False
    whatsapp_url: Optional[str] = None
    email_available: bool = False
    email_draft: Optional[Dict[str, Any]] = None
    latest_pitch: Optional[Dict[str, Any]] = None
    pitch_channel: Optional[str] = None
    pitch_status: Optional[str] = None


class SalesLeadDetailResponse(BaseModel):
    lead: Lead
    business: Business
    latest_research: Optional[Dict[str, Any]] = None
    latest_verification: Optional[str] = None
    latest_website_audit: Optional[Dict[str, Any]] = None
    qualification: Qualification
    latest_outreach: Optional[Outreach] = None
    all_outreach: List[Outreach] = Field(default_factory=list)
    conversation_metadata: Optional[Dict[str, Any]] = None
    pipeline_state: Dict[str, Any]
    readiness_flags: ReadinessFlags
    next_recommended_action: str
    contact_action_data: ContactActionData


class TimelineEvent(BaseModel):
    event_type: str
    title: str
    description: Optional[str] = None
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None


class LeadTimelineResponse(BaseModel):
    lead_id: str
    events: List[TimelineEvent]


class SalesActionRequest(BaseModel):
    force_refresh: bool = False
    channel: Optional[OutreachChannel] = OutreachChannel.EMAIL


class SalesActionResponse(BaseModel):
    success: bool
    action: str
    lead_id: str
    message: str
    result: Optional[Dict[str, Any]] = None
