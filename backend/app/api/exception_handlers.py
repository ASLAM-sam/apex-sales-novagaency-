from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import (
    AegisBaseException,
    ConflictError,
    DatabaseError,
    InvalidObjectIdError,
    NotFoundError,
    ValidationError,
)
from app.schemas.api import ErrorDetail, ErrorResponseEnvelope


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFoundError)
    async def not_found_exception_handler(request: Request, exc: NotFoundError):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="NOT_FOUND", message=exc.message)
            ).model_dump(),
        )

    @app.exception_handler(ConflictError)
    async def conflict_exception_handler(request: Request, exc: ConflictError):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="CONFLICT", message=exc.message)
            ).model_dump(),
        )

    @app.exception_handler(InvalidObjectIdError)
    async def invalid_id_exception_handler(request: Request, exc: InvalidObjectIdError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="INVALID_ID", message=exc.message)
            ).model_dump(),
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="VALIDATION_ERROR", message=exc.message)
            ).model_dump(),
        )

    @app.exception_handler(DatabaseError)
    async def database_exception_handler(request: Request, exc: DatabaseError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(
                    code="DATABASE_UNAVAILABLE",
                    message="Database service is currently unavailable.",
                )
            ).model_dump(),
        )

    @app.exception_handler(AegisBaseException)
    async def aegis_base_exception_handler(request: Request, exc: AegisBaseException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="INTERNAL_ERROR", message=exc.message)
            ).model_dump(),
        )
