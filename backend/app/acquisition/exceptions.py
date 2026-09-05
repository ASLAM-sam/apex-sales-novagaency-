class AcquisitionError(Exception):
    """Base exception for lead acquisition errors."""

    pass


class UnsupportedAcquisitionSourceError(AcquisitionError):
    """Raised when an unsupported lead acquisition source is requested."""

    pass


class CandidateValidationError(AcquisitionError):
    """Raised when a candidate business record fails validation."""

    pass
