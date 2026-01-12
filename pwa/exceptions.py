"""
Custom exceptions for PWA CLI.
"""


class PWAError(Exception):
    """Base exception for all PWA errors."""

    pass


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

    pass


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
