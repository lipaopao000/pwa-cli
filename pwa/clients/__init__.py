"""
Client modules for external services

This package contains client implementations for various external services.
"""

from .markitdown import MarkItDownClient, convert_to_markdown
from .mineru import MineruClient
from .pubmed import PubMedClient
from .ragflow import RagFlowClient as RAGFlowClient
from .zotero import ZoteroClient, fetch_preferred_references

__all__ = [
    "MarkItDownClient",
    "convert_to_markdown",
    "MineruClient",
    "PubMedClient",
    "RAGFlowClient",
    "ZoteroClient",
    "fetch_preferred_references",
]
