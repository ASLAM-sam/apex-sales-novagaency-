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
from app.llm.exceptions import (
    LLMAuthenticationError,
    LLMConfigurationError,
    LLMConnectionError,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMUpstreamError,
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

    @app.exception_handler(LLMConfigurationError)
    async def llm_config_exception_handler(request: Request, exc: LLMConfigurationError):
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="LLM_NOT_CONFIGURED", message="AI service is not configured.")
            ).model_dump(),
        )

    @app.exception_handler(LLMAuthenticationError)
    async def llm_auth_exception_handler(request: Request, exc: LLMAuthenticationError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="LLM_AUTH_FAILED", message="AI service authentication failed.")
            ).model_dump(),
        )

    @app.exception_handler(LLMTimeoutError)
    async def llm_timeout_exception_handler(request: Request, exc: LLMTimeoutError):
        return JSONResponse(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="LLM_TIMEOUT", message="AI service timed out. Please try again.")
            ).model_dump(),
        )

    @app.exception_handler(LLMRateLimitError)
    async def llm_rate_limit_exception_handler(request: Request, exc: LLMRateLimitError):
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="LLM_RATE_LIMITED", message="AI service is busy. Please wait and try again.")
            ).model_dump(),
        )

    @app.exception_handler(LLMConnectionError)
    async def llm_connection_exception_handler(request: Request, exc: LLMConnectionError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="LLM_UNAVAILABLE", message="AI service is currently unavailable.")
            ).model_dump(),
        )

    @app.exception_handler(LLMUpstreamError)
    async def llm_upstream_exception_handler(request: Request, exc: LLMUpstreamError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="LLM_UPSTREAM_ERROR", message="AI service returned an error.")
            ).model_dump(),
        )

    @app.exception_handler(LLMError)
    async def llm_exception_handler(request: Request, exc: LLMError):
        return JSONResponse(
            status_code=status.HTTP_502_BAD_GATEWAY,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="LLM_ERROR", message="AI request failed.")
            ).model_dump(),
        )

    @app.exception_handler(AegisBaseException)
    async def aegis_base_exception_handler(request: Request, exc: AegisBaseException):
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponseEnvelope(
                error=ErrorDetail(code="INTERNAL_ERROR", message="An unexpected error occurred.")
            ).model_dump(),
        )
