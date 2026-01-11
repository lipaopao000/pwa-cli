"""
Tests for references command
"""

import pytest
import tempfile
import json
from pathlib import Path

from pwa.config import ConfigManager
from pwa.commands.references import ReferencesMatchCommand


class TestReferencesMatchCommand:
    """Test ReferencesMatchCommand class"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def config_manager(self, temp_dir):
        """Create ConfigManager instance"""
        return ConfigManager(config_dir=temp_dir)
    
    @pytest.fixture
    def command(self, config_manager):
        """Create ReferencesMatchCommand instance"""
        return ReferencesMatchCommand(config_manager)
    
    def test_init(self, command):
        """Test command initialization"""
        assert command.name == "references_match"
        assert command.description == "匹配参考文献"
    
    def test_extract_title_quoted(self, command):
        """Test extracting quoted title"""
        line = 'Smith J. "This is the title" Journal 2023;10:123-456.'
        title = command._extract_title(line)
        assert title == "This is the title"
    
    def test_extract_title_split(self, command):
        """Test extracting title using split logic"""
        line = 'Smith J. This is the title. Journal of Medicine. 2023;10:123-456.'
        title = command._extract_title(line)
        assert "This is the title" in title
    
    def test_extract_doi_url(self, command):
        """Test extracting DOI and URL"""
        line = 'Title here. doi:10.1234/test https://example.com/article'
        doi, url = command._extract_doi_url(line)
        
        assert doi == 'https://doi.org/10.1234/test'
        assert url == 'https://example.com/article'
    
    def test_parse_citation_string_single(self, command):
        """Test parsing single citation"""
        result = command._parse_citation_string("1")
        assert result == ["1"]
    
    def test_parse_citation_string_multiple(self, command):
        """Test parsing multiple citations"""
        result = command._parse_citation_string("1,2,3")
        assert result == ["1", "2", "3"]
    
    def test_parse_citation_string_range(self, command):
        """Test parsing range citation"""
        result = command._parse_citation_string("1-5")
        assert result == ["1", "2", "3", "4", "5"]
    
    def test_parse_citation_string_mixed(self, command):
        """Test parsing mixed citations"""
        result = command._parse_citation_string("1,3-5,7")
        assert result == ["1", "3", "4", "5", "7"]
    
    def test_extract_references_from_md(self, command):
        """Test extracting references from Markdown"""
        md_content = """
# Paper Title

## Abstract
This is the abstract.

## References

[1] Smith J. "First paper title" Journal 2023;10:123-456.
[2] Jones A. Second paper title. Nature. 2022;20:789-800.
"""
        
        refs, details = command.extract_references_from_md(md_content)
        
        assert len(refs) == 2
        assert "1" in refs
        assert "2" in refs
        assert "First paper title" in refs["1"]["title"]
        assert "Second paper title" in refs["2"]["title"]


class TestReferencesMatchCommandIntegration:
    """Integration tests for ReferencesMatchCommand"""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def sample_markdown(self, temp_dir):
        """Create sample markdown file"""
        md_file = temp_dir / "paper.md"
        md_content = """
# Test Paper

## Abstract
This is a test paper.

## References

[1] Smith J. "Test paper title" Journal 2023;10:123-456. doi:10.1234/test
"""
        md_file.write_text(md_content)
        return md_file
    
    @pytest.fixture
    def sample_bibtex(self, temp_dir):
        """Create sample BibTeX file"""
        bib_file = temp_dir / "references.bib"
        bib_content = """
@article{smith2023test,
  title={Test paper title},
  author={Smith, J},
  journal={Journal},
  year={2023},
  doi={10.1234/test}
}
"""
        bib_file.write_text(bib_content)
        return bib_file
    
    def test_validate_valid_params(self, temp_dir, sample_markdown):
        """Test validation with valid parameters"""
        config_manager = ConfigManager(config_dir=temp_dir)
        command = ReferencesMatchCommand(config_manager)
        
        assert command.validate(md_file=sample_markdown)
    
    def test_validate_invalid_md_file(self, temp_dir):
        """Test validation with invalid markdown file"""
        config_manager = ConfigManager(config_dir=temp_dir)
        command = ReferencesMatchCommand(config_manager)
        
        assert not command.validate(md_file=Path("nonexistent.md"))
