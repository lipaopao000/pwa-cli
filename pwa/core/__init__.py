"""
Core functionality modules for PWA

This package contains core utilities and clients for PWA-CLI.
"""

from .utils import (
    load_markdown_content,
    calculate_jaccard_similarity,
    normalize_doi,
    parse_biblatex_content,
    parse_json_content,
)

from .zotero_client import (
    ZoteroClient,
    fetch_preferred_references,
)

__all__ = [
    # Utils
    'load_markdown_content',
    'calculate_jaccard_similarity',
    'normalize_doi',
    'parse_biblatex_content',
    'parse_json_content',
    
    # Zotero Client
    'ZoteroClient',
    'fetch_preferred_references',
    
    # Module references (for direct import)
    'ragflow_client',
    'pubmed_client',
    'statement_verifier',
    'statement_verifier_utils',
    'configuration',
    'state',
    'schemas',
    'prompts',
    'base_agent',
    'citation_agent',
]
