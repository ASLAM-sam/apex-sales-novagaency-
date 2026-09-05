from app.core.exceptions import AegisBaseException


class DiscoveryError(AegisBaseException):
    """Base exception class for lead discovery errors."""

    def __init__(self, message: str = "A discovery error occurred."):
        super().__init__(message)


class InvalidDiscoveryRequestError(DiscoveryError):
    """Raised when a discovery search request is invalid."""

    pass


class UnsupportedDiscoverySourceError(DiscoveryError):
    """Raised when an requested discovery source is not supported or registered."""

    pass
