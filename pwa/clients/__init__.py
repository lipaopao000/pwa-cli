"""
External service clients for PWA
"""

# Import clients from core module for backward compatibility
from ..core.zotero_client import fetch_preferred_references
from ..core.pubmed_client import PubMedClient
from ..core.ragflow_client import RagFlowClient

__all__ = [
    'fetch_preferred_references',
    'PubMedClient',
    'RagFlowClient',
]
