class AegisBaseException(Exception):
    """Base exception class for Apex Sales AI application."""

    def __init__(self, message: str = "An application error occurred."):
        self.message = message
        super().__init__(self.message)


class ValidationError(AegisBaseException):
    """Raised when data validation fails."""

    def __init__(self, message: str = "Validation error occurred."):
        super().__init__(message)


class InvalidObjectIdError(ValidationError):
    """Raised when an invalid ObjectId format is provided."""

    def __init__(self, message: str = "Invalid ID format provided."):
        super().__init__(message)


class NotFoundError(AegisBaseException):
    """Raised when a requested resource is not found."""

    def __init__(self, message: str = "Resource not found."):
        super().__init__(message)


class ConflictError(AegisBaseException):
    """Raised when a conflict occurs (e.g. duplicate resource)."""

    def __init__(self, message: str = "Resource conflict occurred."):
        super().__init__(message)


class ExternalServiceError(AegisBaseException):
    """Raised when an external service call fails."""

    def __init__(self, message: str = "External service error occurred."):
        super().__init__(message)


class ConfigurationError(AegisBaseException):
    """Raised when there is an invalid or missing configuration."""

    def __init__(self, message: str = "Configuration error occurred."):
        super().__init__(message)


class DatabaseError(AegisBaseException):
    """Raised when a database error occurs."""

    def __init__(self, message: str = "Database error occurred."):
        super().__init__(message)


