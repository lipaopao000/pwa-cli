"""
Tests for fulltext command
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from pwa.config import ConfigManager
from pwa.commands.fulltext import FullTextDownloadCommand, FullTextStatusCommand


class TestFullTextDownloadCommand:
    """Test FullTextDownloadCommand class"""
    
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
        """Create FullTextDownloadCommand instance"""
        return FullTextDownloadCommand(config_manager)
    
    def test_init(self, command):
        """Test command initialization"""
        assert command.name == "fulltext_download"
        assert command.description == "下载论文全文 Markdown"
    
    def test_validate_missing_ocr_config(self, command):
        """Test validation with missing OCR config"""
        assert not command.validate(ref_source="zotero")
    
    def test_validate_with_bibtex_file(self, command, temp_dir):
        """Test validation with BibTeX file"""
        # Create test BibTeX file
        bib_file = temp_dir / "test.bib"
        bib_file.write_text("@article{test2023, title={Test}}")
        
        # Create OCR config
        command.config_manager.save_config('ocr', {'mineru_api_token': 'test_token'})
        
        assert command.validate(ref_source="bibtex", ref_path=str(bib_file))
    
    def test_validate_missing_bibtex_file(self, command):
        """Test validation with missing BibTeX file"""
        command.config_manager.save_config('ocr', {'mineru_api_token': 'test_token'})
        assert not command.validate(ref_source="bibtex", ref_path="nonexistent.bib")


class TestFullTextStatusCommand:
    """Test FullTextStatusCommand class"""
    
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
        """Create FullTextStatusCommand instance"""
        return FullTextStatusCommand(config_manager)
    
    def test_init(self, command):
        """Test command initialization"""
        assert command.name == "fulltext_status"
        assert command.description == "查看全文下载状态"
    
    def test_execute_no_tasks(self, command):
        """Test execution with no tasks"""
        result = command.execute()
        assert result['status'] == 'no_tasks'
