from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import AliasChoices, Field
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now
from app.schemas.enums import CampaignStatus, ServiceType


class Campaign(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")

    name: str
    description: Optional[str] = None

    status: CampaignStatus = CampaignStatus.DRAFT

    target_service: Optional[ServiceType] = None
    target_industry: Optional[str] = None

    lead_filters: Dict[str, Any] = Field(default_factory=dict)

    total_leads: int = 0
    contacted_count: int = 0
    replied_count: int = 0
    interested_count: int = 0
    converted_count: int = 0

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
