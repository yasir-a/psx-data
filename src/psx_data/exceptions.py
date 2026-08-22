"""Custom exceptions for psx-data."""


class PSXError(Exception):
    """Base exception for all psx-data errors."""
    pass


class PSXNetworkError(PSXError):
    """Raised when an HTTP or network request fails."""
    pass


class PSXParseError(PSXError):
    """Raised when response parsing fails."""
    pass