from datetime import datetime
from typing import List, Optional
from pydantic import AliasChoices, Field
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now
from app.schemas.enums import BusinessStatus, VerificationStatus


class SocialProfiles(MongoBaseModel):
    instagram: Optional[str] = None
    facebook: Optional[str] = None
    linkedin: Optional[str] = None
    youtube: Optional[str] = None
    other: List[str] = Field(default_factory=list)


class SourceRecord(MongoBaseModel):
    source_type: str
    source_url: Optional[str] = None
    source_name: Optional[str] = None
    discovered_at: datetime = Field(default_factory=utc_now)


class Business(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")

    name: str
    normalized_name: Optional[str] = None

    description: Optional[str] = None

    category: Optional[str] = None
    sub_category: Optional[str] = None

    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None

    website: Optional[str] = None
    normalized_domain: Optional[str] = None

    phone: Optional[str] = None
    normalized_phone: Optional[str] = None

    email: Optional[str] = None

    social_profiles: SocialProfiles = Field(default_factory=SocialProfiles)
    source_records: List[SourceRecord] = Field(default_factory=list)

    business_status: BusinessStatus = BusinessStatus.UNKNOWN
    verification_status: VerificationStatus = VerificationStatus.UNVERIFIED

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
