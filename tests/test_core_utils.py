"""
Tests for core utilities
"""

import pytest

from pwa.core.utils import calculate_jaccard_similarity, extract_doi, normalize_title


class TestCalculateJaccardSimilarity:
    """Tests for Jaccard similarity calculation."""

    def test_identical_strings(self):
        """Test similarity of identical strings."""
        similarity = calculate_jaccard_similarity("test string", "test string")
        assert similarity == 1.0

    def test_completely_different_strings(self):
        """Test similarity of completely different strings."""
        similarity = calculate_jaccard_similarity("abc", "xyz")
        assert similarity == 0.0

    def test_partial_overlap(self):
        """Test similarity of partially overlapping strings."""
        similarity = calculate_jaccard_similarity("hello world", "hello python")
        assert 0.0 < similarity < 1.0

    def test_case_insensitive(self):
        """Test that comparison is case-insensitive."""
        similarity = calculate_jaccard_similarity("Hello World", "hello world")
        assert similarity == 1.0

    def test_empty_strings(self):
        """Test handling of empty strings."""
        similarity = calculate_jaccard_similarity("", "")
        assert similarity == 0.0

    def test_one_empty_string(self):
        """Test handling when one string is empty."""
        similarity = calculate_jaccard_similarity("test", "")
        assert similarity == 0.0


class TestExtractDOI:
    """Tests for DOI extraction."""

    def test_extract_valid_doi(self):
        """Test extracting valid DOI."""
        text = "This paper has DOI: 10.1234/test.2023.001"
        doi = extract_doi(text)
        assert doi == "10.1234/test.2023.001"

    def test_extract_doi_with_url(self):
        """Test extracting DOI from URL."""
        text = "Available at https://doi.org/10.1234/test.2023.001"
        doi = extract_doi(text)
        assert doi == "10.1234/test.2023.001"

    def test_extract_doi_with_dx_url(self):
        """Test extracting DOI from dx.doi.org URL."""
        text = "See http://dx.doi.org/10.1234/test.2023.001"
        doi = extract_doi(text)
        assert doi == "10.1234/test.2023.001"

    def test_no_doi_found(self):
        """Test when no DOI is present."""
        text = "This text has no DOI"
        doi = extract_doi(text)
        assert doi is None

    def test_multiple_dois(self):
        """Test extracting first DOI when multiple are present."""
        text = "First DOI: 10.1234/test1 and second DOI: 10.5678/test2"
        doi = extract_doi(text)
        assert doi == "10.1234/test1"

    def test_doi_with_special_characters(self):
        """Test DOI with special characters."""
        text = "DOI: 10.1234/test(2023)001-002"
        doi = extract_doi(text)
        assert doi is not None
        assert doi.startswith("10.1234/")


class TestNormalizeTitle:
    """Tests for title normalization."""

    def test_basic_normalization(self):
        """Test basic title normalization."""
        title = "  Test Title  "
        normalized = normalize_title(title)
        assert normalized == "test title"

    def test_remove_punctuation(self):
        """Test removing punctuation."""
        title = "Test: Title, with Punctuation!"
        normalized = normalize_title(title)
        assert ":" not in normalized
        assert "," not in normalized
        assert "!" not in normalized

    def test_multiple_spaces(self):
        """Test handling multiple spaces."""
        title = "Test    Title    with    Spaces"
        normalized = normalize_title(title)
        assert "    " not in normalized
        assert normalized == "test title with spaces"

    def test_lowercase_conversion(self):
        """Test lowercase conversion."""
        title = "TEST TITLE IN UPPERCASE"
        normalized = normalize_title(title)
        assert normalized == "test title in uppercase"

    def test_empty_title(self):
        """Test handling empty title."""
        normalized = normalize_title("")
        assert normalized == ""

    def test_unicode_characters(self):
        """Test handling unicode characters."""
        title = "Tëst Tïtlé with Üñíçödé"
        normalized = normalize_title(title)
        assert isinstance(normalized, str)
        assert len(normalized) > 0
