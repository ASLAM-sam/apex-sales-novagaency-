from datetime import datetime
from typing import Optional
from pydantic import AliasChoices, Field
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now
from app.schemas.enums import AgentRunStatus, AgentType


class AgentRun(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")

    agent_type: AgentType
    run_type: Optional[str] = None

    status: AgentRunStatus = AgentRunStatus.QUEUED

    lead_id: Optional[PyObjectId] = None
    business_id: Optional[PyObjectId] = None
    campaign_id: Optional[PyObjectId] = None

    input_reference: Optional[str] = None
    output_reference: Optional[str] = None

    model_provider: Optional[str] = None
    model_name: Optional[str] = None

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    duration_ms: Optional[int] = None

    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None

    error_code: Optional[str] = None
    error_message: Optional[str] = None

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
