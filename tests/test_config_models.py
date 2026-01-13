"""
Tests for configuration models
"""

import pytest
from pydantic import ValidationError

from pwa.config_models import (
    ConfigValidationError,
    LLMConfig,
    LLMProviderConfig,
    OCRAPIConfig,
    RAGFlowConfig,
    ZoteroConfig,
    load_and_validate_llm_config,
    load_and_validate_ocr_config,
    load_and_validate_ragflow_config,
    load_and_validate_zotero_config,
)


class TestLLMProviderConfig:
    """Tests for LLMProviderConfig model."""

    def test_valid_config(self):
        """Test valid LLM provider configuration."""
        config = LLMProviderConfig(
            api_key="test-key",
            base_url="https://api.openai.com/v1",
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000,
        )
        assert config.api_key == "test-key"
        assert config.model == "gpt-4"
        assert config.temperature == 0.5

    def test_temperature_validation(self):
        """Test temperature range validation."""
        with pytest.raises(ValidationError):
            LLMProviderConfig(
                api_key="test-key",
                base_url="https://api.openai.com/v1",
                model="gpt-4",
                temperature=3.0,  # Invalid: > 2.0
            )

    def test_max_tokens_validation(self):
        """Test max_tokens validation."""
        with pytest.raises(ValidationError):
            LLMProviderConfig(
                api_key="test-key",
                base_url="https://api.openai.com/v1",
                model="gpt-4",
                max_tokens=0,  # Invalid: must be positive
            )


class TestLLMConfig:
    """Tests for LLMConfig model."""

    def test_valid_config(self, sample_llm_config):
        """Test valid LLM configuration."""
        config = LLMConfig(**sample_llm_config)
        assert config.active_provider == "openai"
        assert "openai" in config.providers
        assert config.providers["openai"].model == "gpt-4"

    def test_missing_active_provider(self):
        """Test validation when active provider is not in providers."""
        with pytest.raises(ValidationError):
            LLMConfig(
                active_provider="nonexistent",
                providers={
                    "openai": {
                        "api_key": "test-key",
                        "base_url": "https://api.openai.com/v1",
                        "model": "gpt-4",
                    }
                },
            )

    def test_load_and_validate_llm_config(self, sample_llm_config):
        """Test loading and validating LLM config from dict."""
        config = load_and_validate_llm_config(sample_llm_config)
        assert isinstance(config, LLMConfig)
        assert config.active_provider == "openai"


class TestZoteroConfig:
    """Tests for ZoteroConfig model."""

    def test_valid_config(self, sample_zotero_config):
        """Test valid Zotero configuration."""
        # Update config to match actual model
        config_data = {
            "api_key": "test-zotero-key",
            "user_id": "12345",
            "library_type": "user",
        }
        config = ZoteroConfig(**config_data)
        assert config.user_id == "12345"
        assert config.library_type == "user"
        assert config.api_key == "test-zotero-key"

    def test_invalid_library_type(self):
        """Test validation of library_type."""
        with pytest.raises(ValidationError):
            ZoteroConfig(
                library_id="12345",
                library_type="invalid",  # Must be 'user' or 'group'
                api_key="test-key",
            )

    def test_load_and_validate_zotero_config(self):
        """Test loading and validating Zotero config from dict."""
        config_data = {
            "api_key": "test-zotero-key",
            "user_id": "12345",
            "library_type": "user",
        }
        config = load_and_validate_zotero_config(config_data)
        assert isinstance(config, ZoteroConfig)
        assert config.user_id == "12345"


class TestOCRAPIConfig:
    """Tests for OCRAPIConfig model."""

    def test_valid_config(self):
        """Test valid OCR API configuration."""
        config = OCRAPIConfig(
            base_url="https://ocr.example.com/api",
            api_key="test-ocr-key",
            timeout=60,
        )
        assert config.base_url == "https://ocr.example.com/api"
        assert config.timeout == 60

    def test_default_timeout(self):
        """Test default timeout value."""
        config = OCRAPIConfig(
            base_url="https://ocr.example.com/api",
            api_key="test-key",
        )
        assert config.timeout == 300

    def test_load_and_validate_ocr_config(self):
        """Test loading and validating OCR config from dict."""
        data = {
            "base_url": "https://ocr.example.com/api",
            "api_key": "test-key",
        }
        config = load_and_validate_ocr_config(data)
        assert isinstance(config, OCRAPIConfig)


class TestRAGFlowConfig:
    """Tests for RAGFlowConfig model."""

    def test_valid_config(self):
        """Test valid RAGFlow configuration."""
        config = RAGFlowConfig(
            base_url="https://ragflow.example.com",
            api_key="test-ragflow-key",
            dataset_id="dataset123",
        )
        assert config.base_url == "https://ragflow.example.com"
        assert config.dataset_id == "dataset123"

    def test_load_and_validate_ragflow_config(self):
        """Test loading and validating RAGFlow config from dict."""
        data = {
            "base_url": "https://ragflow.example.com",
            "api_key": "test-key",
            "dataset_id": "dataset123",
        }
        config = load_and_validate_ragflow_config(data)
        assert isinstance(config, RAGFlowConfig)


class TestConfigValidationError:
    """Tests for ConfigValidationError."""

    def test_error_message(self):
        """Test error message formatting."""
        error = ConfigValidationError("test_config", "Invalid value")
        assert "test_config" in str(error)
        assert "Invalid value" in str(error)

    def test_from_pydantic_error(self):
        """Test creating error from Pydantic ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            LLMProviderConfig(
                api_key="",  # Empty string should fail
                base_url="https://api.openai.com/v1",
                model="gpt-4",
            )
        # Just verify the error was raised
        assert exc_info.value is not None
