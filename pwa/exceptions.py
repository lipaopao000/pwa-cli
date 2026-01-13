"""Custom exceptions for PWA CLI.
"""

from typing import Optional


class PWAError(Exception):
    """Base exception for all PWA errors."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ConfigurationError(PWAError):
    """Raised when there is a configuration error."""

    pass


class ValidationError(PWAError):
    """Raised when validation fails."""

    pass


class FileNotFoundError(PWAError):
    """Raised when a required file is not found."""

    pass


class APIError(PWAError):
    """Base class for API-related errors."""

    def __init__(self, message: str, status_code: Optional[int] = None, details: Optional[dict] = None):
        super().__init__(message, details)
        self.status_code = status_code


class AuthenticationError(APIError):
    """Raised when authentication fails."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=401, details=details)


class RateLimitError(APIError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, status_code=429, details=details)


class NetworkError(APIError):
    """Raised when network operation fails."""

    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message, details=details)


class ZoteroAPIError(APIError):
    """Raised when Zotero API call fails."""

    pass


class OCRAPIError(APIError):
    """Raised when OCR API call fails."""

    pass


class RAGFlowAPIError(APIError):
    """Raised when RAGFlow API call fails."""

    pass


class PubMedAPIError(APIError):
    """Raised when PubMed API call fails."""

    pass


class LLMError(PWAError):
    """Raised when LLM operation fails."""

    pass


class ParsingError(PWAError):
    """Raised when parsing fails."""

    pass


class ReferenceMatchingError(PWAError):
    """Raised when reference matching fails."""

    pass


class SessionError(PWAError):
    """Raised when session operation fails."""

    pass


class CommandExecutionError(PWAError):
    """Raised when command execution fails."""

    pass


class WorkflowError(PWAError):
    """Raised when workflow execution fails."""

    pass
