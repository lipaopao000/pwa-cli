"""
Configuration management for PWA CLI
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import shutil


class ConfigManager:
    """Manages configuration files and directories"""
    
    # Default config directory locations (in order of priority)
    CONFIG_LOCATIONS = [
        lambda: Path.cwd() / "config-and-cache",  # Project level
        lambda: Path.home() / ".config" / "pwa",  # User level
        lambda: Path("/etc/pwa"),                 # System level
    ]
    
    # Default config file names
    DEFAULT_CONFIGS = {
        'llm': 'llm_config.yaml',
        'zotero': 'zotero_config.yaml',
        'ocr': 'OCR_API.yaml',
        'ragflow': 'RAGFlow.yaml',
    }
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize configuration manager
        
        Args:
            config_dir: Custom configuration directory. If None, uses default locations.
        """
        if config_dir:
            self.config_dir = Path(config_dir)
        else:
            self.config_dir = self._find_or_create_config_dir()
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def _find_or_create_config_dir(self) -> Path:
        """Find existing config directory or create user-level one"""
        # Check if any config location exists
        for location_func in self.CONFIG_LOCATIONS:
            try:
                location = location_func()
                if location.exists():
                    return location
            except Exception:
                continue
        
        # Create user-level config directory
        user_config = Path.home() / ".config" / "pwa"
        user_config.mkdir(parents=True, exist_ok=True)
        return user_config
    
    def get_config_path(self, name: str) -> Path:
        """
        Get path to a configuration file
        
        Args:
            name: Config name (e.g., 'llm', 'zotero') or filename
        
        Returns:
            Path to the configuration file
        """
        # If name is a known config key, use the default filename
        if name in self.DEFAULT_CONFIGS:
            filename = self.DEFAULT_CONFIGS[name]
        else:
            filename = name if name.endswith('.yaml') else f"{name}.yaml"
        
        return self.config_dir / filename
    
    def load_config(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Load a configuration file
        
        Args:
            name: Config name or filename
        
        Returns:
            Configuration dictionary or None if not found
        """
        config_path = self.get_config_path(name)
        
        if not config_path.exists():
            return None
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            from .ui import print_warning
            print_warning(f"加载配置文件失败 {config_path}: {e}")
            return None
    
    def save_config(self, name: str, data: Dict[str, Any]):
        """
        Save a configuration file
        
        Args:
            name: Config name or filename
            data: Configuration data to save
        """
        config_path = self.get_config_path(name)
        
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.safe_dump(data, f, default_flow_style=False, allow_unicode=True)
        except Exception as e:
            from .ui import print_error
            print_error(f"保存配置文件失败 {config_path}: {e}")
            raise
    
    def ensure_config(self, name: str, source_path: Optional[Path] = None) -> Path:
        """
        Ensure a configuration file exists, copying from source if needed
        
        Args:
            name: Config name
            source_path: Source file to copy from if config doesn't exist
        
        Returns:
            Path to the configuration file
        """
        config_path = self.get_config_path(name)
        
        if not config_path.exists() and source_path and source_path.exists():
            try:
                shutil.copy2(source_path, config_path)
                from .ui import print_success
                print_success(f"已创建配置文件: {config_path}")
            except Exception as e:
                from .ui import print_warning
                print_warning(f"复制配置文件失败: {e}")
        
        return config_path
    
    def list_configs(self) -> Dict[str, Path]:
        """
        List all available configuration files
        
        Returns:
            Dictionary mapping config names to their paths
        """
        configs = {}
        
        for name, filename in self.DEFAULT_CONFIGS.items():
            path = self.config_dir / filename
            if path.exists():
                configs[name] = path
        
        # Also include any other YAML files
        for yaml_file in self.config_dir.glob("*.yaml"):
            name = yaml_file.stem
            if name not in configs:
                configs[name] = yaml_file
        
        return configs
    
    def get_cache_dir(self, markdown_file: Optional[Path] = None) -> Path:
        """
        Get cache directory for a specific markdown file or general cache
        
        Args:
            markdown_file: Markdown file to get cache for
        
        Returns:
            Path to cache directory
        """
        if markdown_file:
            # Create cache directory next to the markdown file
            md_path = Path(markdown_file).resolve()
            cache_dir = md_path.parent / "config-and-cache"
        else:
            # Use general cache directory
            cache_dir = self.config_dir / "cache"
        
        cache_dir.mkdir(parents=True, exist_ok=True)
        return cache_dir
    
    def get_output_dir(self, name: str, base_dir: Optional[Path] = None) -> Path:
        """
        Get output directory for a specific purpose
        
        Args:
            name: Output directory name (e.g., 'FullTextMD')
            base_dir: Base directory. If None, uses current directory.
        
        Returns:
            Path to output directory
        """
        if base_dir:
            output_dir = Path(base_dir) / name
        else:
            output_dir = Path.cwd() / name
        
        output_dir.mkdir(parents=True, exist_ok=True)
        return output_dir


def get_default_config_manager() -> ConfigManager:
    """Get default configuration manager instance"""
    return ConfigManager()
