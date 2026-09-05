from datetime import datetime
from typing import Optional
from pydantic import AliasChoices, Field
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now
from app.schemas.enums import ConversationIntent, ConversationStatus, OutreachChannel


class Conversation(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")
    lead_id: PyObjectId
    business_id: PyObjectId

    channel: OutreachChannel
    status: ConversationStatus = ConversationStatus.OPEN
    message_count: int = 0

    last_message_at: Optional[datetime] = None
    last_inbound_at: Optional[datetime] = None
    last_outbound_at: Optional[datetime] = None

    sentiment: Optional[str] = None
    intent: ConversationIntent = ConversationIntent.UNKNOWN

    ai_summary: Optional[str] = None
    next_action: Optional[str] = None
    next_follow_up_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
