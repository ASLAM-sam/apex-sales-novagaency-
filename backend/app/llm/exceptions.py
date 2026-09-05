import re
from app.core.exceptions import AegisBaseException


def sanitize_error_message(message: str) -> str:
    """
    Sanitizes exception messages to ensure API keys, Bearer tokens,
    and authorization headers are never exposed in log outputs or exception messages.
    """
    if not message:
        return ""
    # Redact Bearer tokens
    sanitized = re.sub(r"(Bearer\s+)[A-Za-z0-9_\-\.]+", r"\1[REDACTED]", message, flags=re.IGNORECASE)
    # Redact api_key= / key= query params or headers
    sanitized = re.sub(r"((?:api[-_]?key|key|secret)=)[A-Za-z0-9_\-\.]+", r"\1[REDACTED]", sanitized, flags=re.IGNORECASE)
    return sanitized


class LLMError(AegisBaseException):
    """Base exception for all LLM infrastructure errors."""

    def __init__(self, message: str):
        safe_msg = sanitize_error_message(message)
        super().__init__(safe_msg)


class LLMConfigurationError(LLMError):
    """Raised when OmniRoute or LLM configuration is missing, invalid, or using placeholders."""

    pass


class LLMAuthenticationError(LLMError):
    """Raised when OmniRoute responds with an authentication failure (e.g. 401 Invalid API Key)."""

    pass


class LLMTimeoutError(LLMError):
    """Raised when an LLM request times out."""

    pass


class LLMConnectionError(LLMError):
    """Raised when network connection to the LLM gateway fails."""

    pass


class LLMRateLimitError(LLMError):
    """Raised when the LLM gateway rate limits requests (HTTP 429)."""

    pass


class LLMUpstreamError(LLMError):
    """Raised when the LLM gateway returns a server error (HTTP 5xx) or malformed payload."""

    pass
