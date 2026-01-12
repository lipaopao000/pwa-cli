"""
Pydantic models for configuration validation.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class LLMProviderConfig(BaseModel):
    """Configuration for a single LLM provider."""

    api_key: str = Field(..., description="API key for the LLM provider")
    base_url: str = Field(..., description="Base URL for the API endpoint")
    model: str = Field(..., description="Model name to use")
    temperature: float = Field(default=0.0, ge=0.0, le=2.0, description="Temperature for sampling")
    max_tokens: Optional[int] = Field(
        default=None, ge=1, description="Maximum tokens in response"
    )

    @field_validator("api_key")
    @classmethod
    def validate_api_key(cls, v: str) -> str:
        """Validate API key is not empty."""
        if not v or v.strip() == "":
            raise ValueError("API key cannot be empty")
        return v.strip()


class LLMConfig(BaseModel):
    """Configuration for LLM providers."""

    active_provider: str = Field(..., description="Name of the active provider")
    providers: Dict[str, LLMProviderConfig] = Field(
        ..., description="Dictionary of provider configurations"
    )

    @field_validator("providers")
    @classmethod
    def validate_active_provider_exists(cls, v: Dict[str, LLMProviderConfig], info) -> Dict:
        """Validate that active_provider exists in providers."""
        active = info.data.get("active_provider")
        if active and active not in v:
            raise ValueError(f"Active provider '{active}' not found in providers")
        return v

    def get_active_provider(self) -> LLMProviderConfig:
        """Get the active provider configuration."""
        return self.providers[self.active_provider]


class ZoteroConfig(BaseModel):
    """Configuration for Zotero API."""

    api_key: str = Field(..., description="Zotero API key")
    user_id: str = Field(..., description="Zotero user ID")
    library_type: str = Field(default="user", description="Library type (user or group)")
    collection_id: Optional[str] = Field(default=None, description="Optional collection ID")

    @field_validator("library_type")
    @classmethod
    def validate_library_type(cls, v: str) -> str:
        """Validate library type is valid."""
        if v not in ["user", "group"]:
            raise ValueError("library_type must be 'user' or 'group'")
        return v


class OCRAPIConfig(BaseModel):
    """Configuration for OCR API (Mineru)."""

    api_key: str = Field(..., description="OCR API key")
    base_url: str = Field(..., description="OCR API base URL")
    max_concurrent: int = Field(default=3, ge=1, le=10, description="Max concurrent requests")
    timeout: int = Field(default=300, ge=30, description="Request timeout in seconds")


class RAGFlowConfig(BaseModel):
    """Configuration for RAGFlow knowledge base."""

    api_key: str = Field(..., description="RAGFlow API key")
    base_url: str = Field(..., description="RAGFlow API base URL")
    dataset_id: Optional[str] = Field(default=None, description="Dataset ID to use")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results to retrieve")


class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


def load_and_validate_llm_config(config_data: Dict[str, Any]) -> LLMConfig:
    """
    Load and validate LLM configuration.

    Args:
        config_data: Raw configuration dictionary

    Returns:
        Validated LLMConfig instance

    Raises:
        ConfigValidationError: If validation fails
    """
    try:
        return LLMConfig(**config_data)
    except Exception as e:
        raise ConfigValidationError(f"LLM configuration validation failed: {e}") from e


def load_and_validate_zotero_config(config_data: Dict[str, Any]) -> ZoteroConfig:
    """
    Load and validate Zotero configuration.

    Args:
        config_data: Raw configuration dictionary

    Returns:
        Validated ZoteroConfig instance

    Raises:
        ConfigValidationError: If validation fails
    """
    try:
        return ZoteroConfig(**config_data)
    except Exception as e:
        raise ConfigValidationError(f"Zotero configuration validation failed: {e}") from e


def load_and_validate_ocr_config(config_data: Dict[str, Any]) -> OCRAPIConfig:
    """
    Load and validate OCR API configuration.

    Args:
        config_data: Raw configuration dictionary

    Returns:
        Validated OCRAPIConfig instance

    Raises:
        ConfigValidationError: If validation fails
    """
    try:
        return OCRAPIConfig(**config_data)
    except Exception as e:
        raise ConfigValidationError(f"OCR API configuration validation failed: {e}") from e


def load_and_validate_ragflow_config(config_data: Dict[str, Any]) -> RAGFlowConfig:
    """
    Load and validate RAGFlow configuration.

    Args:
        config_data: Raw configuration dictionary

    Returns:
        Validated RAGFlowConfig instance

    Raises:
        ConfigValidationError: If validation fails
    """
    try:
        return RAGFlowConfig(**config_data)
    except Exception as e:
        raise ConfigValidationError(f"RAGFlow configuration validation failed: {e}") from e
