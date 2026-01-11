"""
Agent modules for PWA-CLI

This package contains AI agent implementations for various tasks.
"""

from .base import BaseAcademicAgent as BaseAgent
from .citation import CitationVerificationAgent as CitationAgent

__all__ = [
    'BaseAgent',
    'CitationAgent',
]
