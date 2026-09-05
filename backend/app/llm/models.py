from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class LLMRole(str, Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


class LLMMessage(BaseModel):
    role: LLMRole
    content: str

    @field_validator("content")
    @classmethod
    def validate_content_non_empty(cls, v: str) -> str:
        if not isinstance(v, str) or not v.strip():
            raise ValueError("LLM message content cannot be empty.")
        return v


class LLMCompletionRequest(BaseModel):
    messages: List[LLMMessage]
    model: Optional[str] = None
    temperature: Optional[float] = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(default=None, gt=0)
    task_type: Optional[str] = "generic"

    @field_validator("messages")
    @classmethod
    def validate_messages_non_empty(cls, v: List[LLMMessage]) -> List[LLMMessage]:
        if not v:
            raise ValueError("LLM completion request must contain at least one message.")
        return v


class LLMTokenUsage(BaseModel):
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None


class LLMCompletionResponse(BaseModel):
    content: str
    model: str
    finish_reason: Optional[str] = "stop"
    usage: Optional[LLMTokenUsage] = None
    raw_response: Optional[Dict[str, Any]] = None
