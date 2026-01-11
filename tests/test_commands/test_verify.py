"""
Tests for verify command
"""

import pytest
import tempfile
import json
from pathlib import Path

from pwa.config import ConfigManager
from pwa.commands.verify import (
    VerifyStatementsCommand,
    VerifyViewResultsCommand,
    VerifyExportReportCommand
)


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
        md_file.write_text("# Test\n\nThis is a test statement.")
        
        assert not command.validate(md_file=str(md_file))
    
    def test_validate_with_configs(self, command, temp_dir):
        """Test validation with all configs"""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test\n\nThis is a test statement [@citation2023].")
        
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
            use_pubmed=False,
            ref_source=None
        )
    
    def test_validate_with_bibtex(self, command, temp_dir):
        """Test validation with BibTeX file"""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test")
        
        bib_file = temp_dir / "test.bib"
        bib_file.write_text("@article{test2023, title={Test}}")
        
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
        
        assert command.validate(
            md_file=str(md_file),
            use_ragflow=False,
            use_pubmed=False,
            ref_source="bibtex",
            ref_path=str(bib_file)
        )
    
    def test_validate_missing_bibtex(self, command, temp_dir):
        """Test validation with missing BibTeX file"""
        md_file = temp_dir / "test.md"
        md_file.write_text("# Test")
        
        command.config_manager.save_config('llm', {
            'active_provider': 'openai',
            'providers': {
                'openai': {
                    'api_key': 'test_key',
                    'model': 'gpt-4o-mini'
                }
            }
        })
        
        assert not command.validate(
            md_file=str(md_file),
            ref_source="bibtex",
            ref_path="nonexistent.bib"
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
        results_file.write_text(json.dumps({"results": []}))
        
        assert command.validate(results_file=str(results_file))
    
    def test_execute_empty_results(self, command, temp_dir):
        """Test execution with empty results"""
        results_file = temp_dir / "results.json"
        results_file.write_text(json.dumps({"results": []}))
        
        result = command.execute(results_file=str(results_file))
        assert result['status'] == 'empty'
    
    def test_execute_with_results(self, command, temp_dir):
        """Test execution with actual results"""
        results_file = temp_dir / "results.json"
        test_results = {
            "results": [
                {
                    "claim_info": {"context": "Test claim 1"},
                    "decision": {"status": "Supported", "reasoning": "Test reasoning"}
                },
                {
                    "claim_info": {"context": "Test claim 2"},
                    "decision": {"status": "Contradicted", "reasoning": "Test reasoning 2"}
                }
            ]
        }
        results_file.write_text(json.dumps(test_results))
        
        result = command.execute(results_file=str(results_file))
        assert result['status'] == 'success'
        assert result['count'] == 2


class TestVerifyExportReportCommand:
    """Test VerifyExportReportCommand class"""
    
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
        """Create VerifyExportReportCommand instance"""
        return VerifyExportReportCommand(config_manager)
    
    def test_init(self, command):
        """Test command initialization"""
        assert command.name == "verify_export_report"
        assert command.description == "导出验证报告"
    
    def test_validate_missing_file(self, command):
        """Test validation with missing results file"""
        assert not command.validate(results_file="nonexistent.json")
    
    def test_validate_with_file(self, command, temp_dir):
        """Test validation with existing file"""
        results_file = temp_dir / "results.json"
        results_file.write_text(json.dumps({"results": []}))
        
        assert command.validate(results_file=str(results_file))
    
    def test_execute_export(self, command, temp_dir):
        """Test report export"""
        results_file = temp_dir / "results.json"
        test_results = {
            "results": [
                {
                    "claim_info": {"context": "Test claim"},
                    "decision": {"status": "Supported", "reasoning": "Test reasoning"},
                    "evidences": [
                        {"source": "test", "content": "test evidence"}
                    ]
                }
            ]
        }
        results_file.write_text(json.dumps(test_results))
        
        output_file = temp_dir / "report.md"
        result = command.execute(
            results_file=str(results_file),
            output_file=str(output_file)
        )
        
        assert result['status'] == 'success'
        assert output_file.exists()
        
        # Check report content
        report_content = output_file.read_text()
        assert "科学陈述验证报告" in report_content
        assert "Test claim" in report_content
        assert "Supported" in report_content
