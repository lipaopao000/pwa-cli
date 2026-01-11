"""
Terminal colors and styling utilities
"""

class Colors:
    """ANSI color codes for terminal output"""
    
    # Basic colors
    BLACK = '\033[30m'
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    
    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Reset
    RESET = '\033[0m'
    
    @classmethod
    def colorize(cls, text, color):
        """Wrap text with color code"""
        return f"{color}{text}{cls.RESET}"
    
    @classmethod
    def success(cls, text):
        """Green text for success messages"""
        return cls.colorize(text, cls.GREEN)
    
    @classmethod
    def error(cls, text):
        """Red text for error messages"""
        return cls.colorize(text, cls.RED)
    
    @classmethod
    def warning(cls, text):
        """Yellow text for warning messages"""
        return cls.colorize(text, cls.YELLOW)
    
    @classmethod
    def info(cls, text):
        """Cyan text for info messages"""
        return cls.colorize(text, cls.CYAN)
    
    @classmethod
    def highlight(cls, text):
        """Bold text for highlighting"""
        return cls.colorize(text, cls.BOLD)


def print_success(message):
    """Print success message in green"""
    print(Colors.success(f"✓ {message}"))


def print_error(message):
    """Print error message in red"""
    print(Colors.error(f"✗ {message}"))


def print_warning(message):
    """Print warning message in yellow"""
    print(Colors.warning(f"⚠ {message}"))


def print_info(message):
    """Print info message in cyan"""
    print(Colors.info(f"ℹ {message}"))
