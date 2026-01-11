"""
Client modules for external services

This package contains client implementations for various external services.
"""

from .mineru import MineruClient
from .pubmed import PubMedClient
from .ragflow import RagFlowClient as RAGFlowClient
from .zotero import ZoteroClient, fetch_preferred_references

__all__ = [
    'MineruClient',
    'PubMedClient',
    'RAGFlowClient',
    'ZoteroClient',
    'fetch_preferred_references',
]
