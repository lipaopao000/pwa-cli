"""
Tests for custom exceptions
"""

import pytest

from pwa.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    LLMError,
    NetworkError,
    ParsingError,
    PWAError,
    RateLimitError,
    ValidationError,
    ZoteroAPIError,
)


class TestPWAError:
    """Tests for base PWAError."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = PWAError("Test error")
        assert str(error) == "Test error"
        assert isinstance(error, Exception)

    def test_error_with_details(self):
        """Test error with additional details."""
        error = PWAError("Test error", details={"key": "value"})
        assert error.details == {"key": "value"}


class TestConfigurationError:
    """Tests for ConfigurationError."""

    def test_configuration_error(self):
        """Test configuration error."""
        error = ConfigurationError("Invalid config")
        assert isinstance(error, PWAError)
        assert "Invalid config" in str(error)


class TestValidationError:
    """Tests for ValidationError."""

    def test_validation_error(self):
        """Test validation error."""
        error = ValidationError("Invalid value")
        assert isinstance(error, PWAError)
        assert "Invalid value" in str(error)


class TestAPIError:
    """Tests for APIError and subclasses."""

    def test_api_error(self):
        """Test basic API error."""
        error = APIError("API failed", status_code=500)
        assert error.status_code == 500
        assert isinstance(error, PWAError)

    def test_authentication_error(self):
        """Test authentication error."""
        error = AuthenticationError("Invalid credentials")
        assert isinstance(error, APIError)
        assert error.status_code == 401

    def test_rate_limit_error(self):
        """Test rate limit error."""
        error = RateLimitError("Too many requests")
        assert isinstance(error, APIError)
        assert error.status_code == 429

    def test_network_error(self):
        """Test network error."""
        error = NetworkError("Connection failed")
        assert isinstance(error, APIError)


class TestZoteroAPIError:
    """Tests for ZoteroAPIError."""

    def test_zotero_error(self):
        """Test Zotero API error."""
        error = ZoteroAPIError("Zotero request failed", status_code=404)
        assert isinstance(error, APIError)
        assert error.status_code == 404


class TestLLMError:
    """Tests for LLMError."""

    def test_llm_error(self):
        """Test LLM error."""
        error = LLMError("Model inference failed")
        assert isinstance(error, PWAError)


class TestParsingError:
    """Tests for ParsingError."""

    def test_parsing_error(self):
        """Test parsing error."""
        error = ParsingError("Failed to parse document")
        assert isinstance(error, PWAError)


class TestErrorHierarchy:
    """Tests for exception hierarchy."""

    def test_catch_base_error(self):
        """Test catching base PWAError."""
        with pytest.raises(PWAError):
            raise ConfigurationError("Test")

    def test_catch_api_error(self):
        """Test catching APIError."""
        with pytest.raises(APIError):
            raise AuthenticationError("Test")

    def test_specific_error_handling(self):
        """Test handling specific error types."""
        try:
            raise RateLimitError("Too many requests")
        except RateLimitError as e:
            assert e.status_code == 429
        except APIError:
            pytest.fail("Should catch RateLimitError specifically")
