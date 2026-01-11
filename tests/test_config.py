"""
Tests for configuration management
"""

import pytest
import tempfile
import yaml
from pathlib import Path

from pwa.config import ConfigManager


class TestConfigManager:
    """Test ConfigManager class"""
    
    @pytest.fixture
    def temp_config_dir(self):
        """Create temporary config directory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)
    
    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create ConfigManager instance with temp directory"""
        return ConfigManager(config_dir=temp_config_dir)
    
    def test_init(self, config_manager, temp_config_dir):
        """Test ConfigManager initialization"""
        assert config_manager.config_dir == temp_config_dir
        assert temp_config_dir.exists()
    
    def test_get_config_path(self, config_manager):
        """Test getting config file path"""
        # Test with known config name
        llm_path = config_manager.get_config_path('llm')
        assert llm_path.name == 'llm_config.yaml'
        
        # Test with filename
        custom_path = config_manager.get_config_path('custom.yaml')
        assert custom_path.name == 'custom.yaml'
        
        # Test with name without extension
        other_path = config_manager.get_config_path('other')
        assert other_path.name == 'other.yaml'
    
    def test_save_and_load_config(self, config_manager):
        """Test saving and loading config"""
        test_data = {
            'key1': 'value1',
            'key2': 123,
            'key3': ['item1', 'item2']
        }
        
        # Save config
        config_manager.save_config('test', test_data)
        
        # Load config
        loaded_data = config_manager.load_config('test')
        
        assert loaded_data == test_data
    
    def test_load_nonexistent_config(self, config_manager):
        """Test loading non-existent config"""
        result = config_manager.load_config('nonexistent')
        assert result is None
    
    def test_ensure_config(self, config_manager, temp_config_dir):
        """Test ensuring config exists"""
        # Create source file
        source_file = temp_config_dir / 'source.yaml'
        source_data = {'test': 'data'}
        with open(source_file, 'w') as f:
            yaml.safe_dump(source_data, f)
        
        # Ensure config (should copy from source)
        result_path = config_manager.ensure_config('test', source_file)
        
        assert result_path.exists()
        
        # Verify content
        loaded = config_manager.load_config('test')
        assert loaded == source_data
    
    def test_list_configs(self, config_manager):
        """Test listing configs"""
        # Create some test configs
        config_manager.save_config('test1', {'data': 1})
        config_manager.save_config('test2', {'data': 2})
        
        configs = config_manager.list_configs()
        
        assert 'test1' in configs
        assert 'test2' in configs
    
    def test_get_cache_dir(self, config_manager, temp_config_dir):
        """Test getting cache directory"""
        # Test with markdown file
        md_file = temp_config_dir / 'test.md'
        md_file.touch()
        
        cache_dir = config_manager.get_cache_dir(md_file)
        
        assert cache_dir.exists()
        assert cache_dir.name == 'config-and-cache'
        assert cache_dir.parent == temp_config_dir
    
    def test_get_output_dir(self, config_manager, temp_config_dir):
        """Test getting output directory"""
        output_dir = config_manager.get_output_dir('FullTextMD', temp_config_dir)
        
        assert output_dir.exists()
        assert output_dir.name == 'FullTextMD'
        assert output_dir.parent == temp_config_dir
