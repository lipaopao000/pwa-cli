"""
Core utility functions for PWA

This package contains core utility functions for data processing.
Agent, client, and verifier modules have been moved to their own packages:
- pwa.agents - Agent implementations
- pwa.clients - External service clients
- pwa.verifier - Statement verification
"""

from .utils import (
    calculate_jaccard_similarity,
    load_markdown_content,
    normalize_doi,
    parse_biblatex_content,
    parse_json_content,
)

__all__ = [
    "load_markdown_content",
    "calculate_jaccard_similarity",
    "normalize_doi",
    "parse_biblatex_content",
    "parse_json_content",
]
