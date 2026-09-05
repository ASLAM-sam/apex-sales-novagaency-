from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AcquisitionCandidateInput(BaseModel):
    name: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    social_profiles: Optional[Dict[str, Any]] = None
    source_name: Optional[str] = "manual"
    source_id: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class AcquisitionLocation(BaseModel):
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class AcquisitionCandidate(BaseModel):
    candidate_id: str
    name: str
    website: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    location: Optional[AcquisitionLocation] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    source: str = "manual"
    already_exists: bool = False
    existing_business_id: Optional[str] = None
    existing_lead_id: Optional[str] = None
    qualification_state: Optional[str] = None
    raw_data: Optional[Dict[str, Any]] = None


class AcquisitionSearchRequest(BaseModel):
    query: Optional[str] = None
    category: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    website_required: bool = False
    limit: int = Field(default=25, ge=1, le=100)
    source: str = "manual"
    manual_candidates: Optional[List[AcquisitionCandidateInput]] = None


class AcquisitionSearchResponse(BaseModel):
    candidates: List[AcquisitionCandidate]
    total: int
    source: str


class AcquisitionImportRequest(BaseModel):
    candidates: List[AcquisitionCandidateInput]


class AcquisitionImportResponse(BaseModel):
    imported: int = 0
    already_exists: int = 0
    duplicates: int = 0
    invalid: int = 0
    failed: int = 0
    business_ids: List[str] = Field(default_factory=list)
    lead_ids: List[str] = Field(default_factory=list)
    details: List[Dict[str, Any]] = Field(default_factory=list)
