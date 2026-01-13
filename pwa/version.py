"""
PWA-CLI Version Information
"""

__all__ = ["__version__", "__author__", "__description__", "__url__", "get_version"]

__version__: str = "1.2.2"
__author__: str = "lipaopao000"
__description__: str = "Paper Writing Assistant - A modern CLI tool for academic writing"
__url__: str = "https://github.com/lipaopao000/pwa-cli"


def get_version() -> str:
    """
    Get the current version string.

    Returns:
        Version string
    """
    return __version__
