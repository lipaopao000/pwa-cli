"""
Base command class for PWA CLI
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from ..config import ConfigManager
from ..ui import print_success, print_error, print_warning, print_info


class BaseCommand(ABC):
    """Base class for all PWA commands"""
    
    # Command metadata
    name: str = ""
    description: str = ""
    help_text: str = ""
    
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize command
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for this command"""
        logger = logging.getLogger(f"pwa.{self.name}")
        logger.setLevel(logging.INFO)
        
        # Add file handler if cache directory exists
        try:
            cache_dir = self.config_manager.config_dir / "logs"
            cache_dir.mkdir(parents=True, exist_ok=True)
            log_file = cache_dir / f"{self.name}.log"
            
            handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
            handler.setLevel(logging.DEBUG)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        except Exception as e:
            print_warning(f"无法设置日志文件: {e}")
        
        return logger
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """
        Execute the command
        
        Args:
            **kwargs: Command-specific arguments
        
        Returns:
            Command execution result
        """
        raise NotImplementedError
    
    def validate(self, **kwargs) -> bool:
        """
        Validate command arguments
        
        Args:
            **kwargs: Command arguments to validate
        
        Returns:
            True if valid, False otherwise
        """
        return True
    
    def get_help(self) -> str:
        """
        Get help text for this command
        
        Returns:
            Help text string
        """
        return self.help_text or self.description
    
    def interactive_execute(self, context: Dict[str, Any] = None):
        """
        Execute command in interactive mode
        
        Args:
            context: Context dictionary from menu system
        
        Returns:
            Execution result
        """
        if context is None:
            context = {}
        
        try:
            # Get parameters interactively
            params = self.get_interactive_params(context)
            
            # Validate parameters
            if not self.validate(**params):
                print_error("参数验证失败")
                return None
            
            # Execute command
            self.logger.info(f"开始执行命令: {self.name}")
            result = self.execute(**params)
            self.logger.info(f"命令执行完成: {self.name}")
            
            return result
            
        except KeyboardInterrupt:
            print_warning("\n操作已取消")
            return None
        except Exception as e:
            self.logger.exception(f"命令执行失败: {e}")
            print_error(f"执行失败: {str(e)}")
            return None
    
    def get_interactive_params(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get command parameters interactively
        
        Args:
            context: Context dictionary
        
        Returns:
            Dictionary of parameters
        """
        # Default implementation - subclasses should override
        return {}
    
    def prompt_input(self, message: str, default: Optional[str] = None) -> str:
        """
        Prompt user for input
        
        Args:
            message: Prompt message
            default: Default value
        
        Returns:
            User input string
        """
        if default:
            prompt = f"{message} [{default}]: "
        else:
            prompt = f"{message}: "
        
        try:
            value = input(prompt).strip()
            return value if value else (default or "")
        except (KeyboardInterrupt, EOFError):
            raise KeyboardInterrupt
    
    def prompt_file(self, message: str, must_exist: bool = True) -> Optional[Path]:
        """
        Prompt user for file path
        
        Args:
            message: Prompt message
            must_exist: Whether file must exist
        
        Returns:
            Path object or None
        """
        while True:
            path_str = self.prompt_input(message)
            if not path_str:
                return None
            
            path = Path(path_str).expanduser().resolve()
            
            if must_exist and not path.exists():
                print_error(f"文件不存在: {path}")
                continue
            
            return path
    
    def prompt_choice(self, message: str, choices: list, default: Optional[str] = None) -> str:
        """
        Prompt user to choose from a list
        
        Args:
            message: Prompt message
            choices: List of choices
            default: Default choice
        
        Returns:
            Selected choice
        """
        print(f"\n{message}")
        for i, choice in enumerate(choices, 1):
            print(f"  {i}. {choice}")
        
        while True:
            choice_str = self.prompt_input("请选择", default)
            
            try:
                choice_idx = int(choice_str) - 1
                if 0 <= choice_idx < len(choices):
                    return choices[choice_idx]
            except ValueError:
                pass
            
            print_error("无效的选择，请重试")
    
    def prompt_confirm(self, message: str, default: bool = True) -> bool:
        """
        Prompt user for yes/no confirmation
        
        Args:
            message: Prompt message
            default: Default value
        
        Returns:
            True for yes, False for no
        """
        default_str = "Y/n" if default else "y/N"
        response = self.prompt_input(f"{message} [{default_str}]", "").lower()
        
        if not response:
            return default
        
        return response in ('y', 'yes', '是')
