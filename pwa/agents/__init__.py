"""
Agent modules for PWA-CLI

This package contains AI agent implementations for various tasks.

Available Agents:
- CitationAgent: Citation and statement verification
"""

from .base import BaseAcademicAgent as BaseAgent
from .citation import CitationAgent, StatementVerifier

__all__ = [
    "BaseAgent",
    "CitationAgent",
    "StatementVerifier",
]
