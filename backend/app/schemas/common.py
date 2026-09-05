from datetime import datetime, timezone
from typing import Annotated, Any, Dict, Optional
from bson import ObjectId
from pydantic import BaseModel, ConfigDict, GetCoreSchemaHandler, field_validator
from pydantic_core import core_schema


def utc_now() -> datetime:
    """Returns current timezone-aware UTC datetime."""
    return datetime.now(timezone.utc)


class _PyObjectIdAnnotation:
    @classmethod
    def __get_pydantic_core_schema__(
        cls, _source_type: Any, _handler: GetCoreSchemaHandler
    ) -> core_schema.CoreSchema:
        def validate(value: Any) -> ObjectId:
            if isinstance(value, ObjectId):
                return value
            if isinstance(value, str) and ObjectId.is_valid(value):
                return ObjectId(value)
            raise ValueError(f"Invalid ObjectId: {value}")

        return core_schema.json_or_python_schema(
            json_schema=core_schema.chain_schema(
                [
                    core_schema.str_schema(),
                    core_schema.no_info_plain_validator_function(validate),
                ]
            ),
            python_schema=core_schema.union_schema(
                [
                    core_schema.is_instance_schema(ObjectId),
                    core_schema.no_info_plain_validator_function(validate),
                ]
            ),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda x: str(x)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls, _core_schema: core_schema.CoreSchema, handler: Any
    ) -> Dict[str, Any]:
        return {"type": "string", "format": "objectid", "example": "60f71b2f9b1d8b2f9b1d8b2f"}


PyObjectId = Annotated[Any, _PyObjectIdAnnotation]


def validate_score_range(v: Optional[float]) -> Optional[float]:
    """Validates that a numeric score is between 0 and 100 inclusive."""
    if v is not None:
        if not (0 <= v <= 100):
            raise ValueError("Score must be between 0 and 100 inclusive.")
    return v


class MongoBaseModel(BaseModel):
    """Base Pydantic model for MongoDB document schemas."""

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_encoders={ObjectId: str, datetime: lambda dt: dt.isoformat()},
    )
