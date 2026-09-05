from datetime import datetime
from typing import List, Optional
from pydantic import AliasChoices, Field, field_validator
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now, validate_score_range
from app.schemas.enums import IssueSeverity


class AuditIssue(MongoBaseModel):
    category: str
    severity: IssueSeverity
    title: str
    description: Optional[str] = None
    evidence: Optional[str] = None
    recommendation: Optional[str] = None


class WebsiteAudit(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")
    business_id: PyObjectId
    lead_id: Optional[PyObjectId] = None

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

    audit_version: str = "1.0"
    audited_at: datetime = Field(default_factory=utc_now)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator(
        "performance_score",
        "seo_score",
        "accessibility_score",
        "design_score",
        "content_score",
        "conversion_score",
        "overall_score",
        mode="before",
    )
    @classmethod
    def check_score(cls, v: Optional[float]) -> Optional[float]:
        return validate_score_range(v)
