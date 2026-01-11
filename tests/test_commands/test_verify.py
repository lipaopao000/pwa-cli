"""
Tests for verify command
"""

import pytest
import tempfile
import json
from pathlib import Path

from pwa.config import ConfigManager
from pwa.commands.verify import VerifyStatementsCommand, VerifyViewResultsCommand


class TestVerifyStatementsCommand:
    """Test VerifyStatementsCommand class"""
    
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
        """Create VerifyStatementsCommand instance"""
        return VerifyStatementsCommand(config_manager)
    
    def test_init(self, command):
        """Test command initialization"""
        assert command.name == "verify_statements"
        assert command.description == "验证科学陈述"
    
    def test_validate_missing_md_file(self, command):
        """Test validation with missing Markdown file"""
        assert not command.validate(md_file="nonexistent.md")
    
    def test_validate_missing_llm_config(self, command, temp_dir):
        """Test validation with missing LLM config"""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test")
        
        assert not command.validate(md_file=str(md_file))
    
    def test_validate_with_configs(self, command, temp_dir):
        """Test validation with all configs"""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test")
        
        # Create configs
        command.config_manager.save_config('llm', {
            'active_provider': 'openai',
            'providers': {
                'openai': {
                    'api_key': 'test_key',
                    'model': 'gpt-4o-mini'
                }
            }
        })
        
        command.config_manager.save_config('ragflow', {
            'ragflow_api_key': 'test_key',
            'ragflow_base_url': 'http://test.com'
        })
        
        assert command.validate(
            md_file=str(md_file),
            use_ragflow=True,
            use_pubmed=False
        )


class TestVerifyViewResultsCommand:
    """Test VerifyViewResultsCommand class"""
    
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
        """Create VerifyViewResultsCommand instance"""
        return VerifyViewResultsCommand(config_manager)
    
    def test_init(self, command):
        """Test command initialization"""
        assert command.name == "verify_view_results"
        assert command.description == "查看验证结果"
    
    def test_validate_missing_file(self, command):
        """Test validation with missing results file"""
        assert not command.validate(results_file="nonexistent.json")
    
    def test_validate_with_file(self, command, temp_dir):
        """Test validation with existing file"""
        results_file = temp_dir / "results.json"
        results_file.write_text("[]")
        
        assert command.validate(results_file=str(results_file))
    
    def test_execute_empty_results(self, command, temp_dir):
        """Test execution with empty results"""
        results_file = temp_dir / "results.json"
        results_file.write_text("[]")
        
        result = command.execute(results_file=str(results_file))
        assert result['status'] == 'empty'
