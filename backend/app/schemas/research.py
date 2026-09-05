from datetime import datetime
from typing import List, Optional
from pydantic import AliasChoices, Field, field_validator
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now, validate_score_range


class ResearchSource(MongoBaseModel):
    source_type: str
    source_url: Optional[str] = None
    title: Optional[str] = None
    retrieved_at: datetime = Field(default_factory=utc_now)


class Research(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")
    business_id: PyObjectId
    lead_id: Optional[PyObjectId] = None

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

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

    @field_validator("research_confidence", mode="before")
    @classmethod
    def check_score(cls, v: Optional[float]) -> Optional[float]:
        return validate_score_range(v)
