from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import AliasChoices, Field
from app.schemas.common import MongoBaseModel, PyObjectId, utc_now
from app.schemas.enums import AIGenerationValidation


class AIGeneration(MongoBaseModel):
    id: Optional[PyObjectId] = Field(default=None, validation_alias=AliasChoices("_id", "id"), serialization_alias="id")

    agent_run_id: Optional[PyObjectId] = None

    task_type: str
    provider: str
    model: str

    prompt_version: Optional[str] = "1.0"
    input_hash: Optional[str] = None

    output_text: Optional[str] = None
    structured_output: Dict[str, Any] = Field(default_factory=dict)

    validation_status: AIGenerationValidation = AIGenerationValidation.PENDING

    tokens_input: Optional[int] = None
    tokens_output: Optional[int] = None

    latency_ms: Optional[int] = None

    created_at: datetime = Field(default_factory=utc_now)
