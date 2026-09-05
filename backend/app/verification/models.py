from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import utc_now
from app.schemas.enums import VerificationStatus


class WebsiteFetchResult(BaseModel):
    accessible: bool = False
    status_code: Optional[int] = None
    final_url: Optional[str] = None
    domain_matches: bool = False
    business_name_found: bool = False
    title: Optional[str] = None
    html_content: Optional[str] = None
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    headers: Dict[str, str] = Field(default_factory=dict)


class VerificationEvidenceItem(BaseModel):
    evidence_type: str
    result: bool
    source: str
    observed_at: datetime = Field(default_factory=utc_now)
    details: Optional[str] = None


class VerificationResult(BaseModel):
    verification_status: VerificationStatus
    business_exists_evidence: bool = False
    website_accessible: bool = False
    domain_matches: bool = False
    business_name_found: bool = False
    phone_present: bool = False
    email_present: bool = False
    evidence_items: List[VerificationEvidenceItem] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=utc_now)
    notes: Optional[str] = None
