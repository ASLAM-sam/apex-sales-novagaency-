from datetime import datetime
from typing import Optional
from pydantic import AliasChoices, Field
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now
from app.schemas.enums import OutreachChannel, OutreachDirection, OutreachMessageType, OutreachStatus


class Outreach(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")
    lead_id: PyObjectId
    business_id: PyObjectId

    channel: OutreachChannel
    direction: OutreachDirection = OutreachDirection.OUTBOUND
    message_type: OutreachMessageType = OutreachMessageType.INITIAL_PITCH

    subject: Optional[str] = None
    message: str

    generated_by: Optional[str] = None
    generation_id: Optional[PyObjectId] = None

    status: OutreachStatus = OutreachStatus.DRAFT

    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    opened_at: Optional[datetime] = None
    replied_at: Optional[datetime] = None
    failure_reason: Optional[str] = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
