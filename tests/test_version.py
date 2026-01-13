"""
Tests for version module
"""

import re

from pwa.version import __version__, get_version


class TestVersion:
    """Tests for version information."""

    def test_version_format(self):
        """Test version string format."""
        # Should follow semantic versioning: MAJOR.MINOR.PATCH
        pattern = r"^\d+\.\d+\.\d+$"
        assert re.match(pattern, __version__), f"Invalid version format: {__version__}"

    def test_get_version(self):
        """Test get_version function."""
        version = get_version()
        assert version == __version__
        assert isinstance(version, str)
        assert len(version) > 0

    def test_version_components(self):
        """Test version components."""
        parts = __version__.split(".")
        assert len(parts) == 3, "Version should have 3 components"

        major, minor, patch = parts
        assert major.isdigit(), "Major version should be numeric"
        assert minor.isdigit(), "Minor version should be numeric"
        assert patch.isdigit(), "Patch version should be numeric"
