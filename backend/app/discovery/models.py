from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.common import utc_now


class DiscoveredCandidate(BaseModel):
    """
    Raw internal candidate representation returned by a discovery source before normalization.
    """

    name: str
    website: Optional[str] = None
    domain: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    social_profiles: Dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=utc_now)


class NormalizedCandidate(BaseModel):
    """
    Candidate representation after deterministic normalization and validation.
    """

    name: str
    normalized_name: str
    website: Optional[str] = None
    normalized_domain: Optional[str] = None
    phone: Optional[str] = None
    normalized_phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    social_profiles: Dict[str, Any] = Field(default_factory=dict)
    source: str = "manual"
    source_id: Optional[str] = None
    source_url: Optional[str] = None
    raw_data: Dict[str, Any] = Field(default_factory=dict)
    discovered_at: datetime = Field(default_factory=utc_now)


class DiscoverySummaryData(BaseModel):
    """
    Summary metrics and created IDs for a completed discovery run.
    """

    run_id: Optional[str] = None
    source: str
    requested: int
    received: int
    valid: int
    duplicates: int
    new_businesses: int
    existing_businesses: int
    new_leads: int
    invalid_candidates: int
    created_business_ids: List[str] = Field(default_factory=list)
    created_lead_ids: List[str] = Field(default_factory=list)
