from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import utc_now
from app.schemas.enums import VerificationStatus
from app.schemas.research import Research
from app.schemas.website_audit import WebsiteAudit


class LeadIntelligenceRequest(BaseModel):
    force_refresh: bool = False


class VerificationSummary(BaseModel):
    verification_status: VerificationStatus
    business_exists_evidence: bool
    website_accessible: bool
    domain_matches: bool
    business_name_found: bool
    phone_present: bool
    email_present: bool
    notes: Optional[str] = None


class WebsiteAuditSummary(BaseModel):
    audit_id: Optional[str] = None
    website_exists: bool
    http_status: Optional[int] = None
    overall_score: Optional[float] = None
    total_issues: int = 0
    high_critical_issues: int = 0
    top_recommendation: Optional[str] = None


class LeadIntelligenceResponse(BaseModel):
    lead_id: str
    business_id: str
    business_name: str
    processing_status: str = "COMPLETED"

    verification: VerificationSummary
    research: Optional[Research] = None
    website_audit: Optional[WebsiteAuditSummary] = None

    run_id: Optional[str] = None
    processed_at: datetime = Field(default_factory=utc_now)
