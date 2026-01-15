"""
WeKnora

This module provides a client for interacting with WeKnora API.
The WeKnora SDK is auto-generated from OpenAPI and placed in weknora_sdk/.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Add WeKnora SDK to Python path
project_root = Path(__file__).parent.parent.parent
weknora_sdk_path = project_root / "pwa" / "clients" / "weknora_sdk"

if weknora_sdk_path.exists() and str(weknora_sdk_path) not in sys.path:
    sys.path.insert(0, str(weknora_sdk_path))
    logger.debug(f"Added WeKnora SDK to path: {weknora_sdk_path}")

try:
    import weknora
    from weknora import ApiClient, Configuration
    from weknora.api.knowledge_api import KnowledgeApi
    from weknora.api.default_api import DefaultApi

    WEKNORA_AVAILABLE = True
except ImportError as e:
    WEKNORA_AVAILABLE = False
    WEKNORA_IMPORT_ERROR = (
        f"Failed to import weknora sdk: {e}\n"
        "Please run: ./scripts/install_weknora_sdk.sh"
    )


class WeKnoraClient:
    """
    Wrapper for WeKnora Python SDK.
    """

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        if not WEKNORA_AVAILABLE:
            raise ImportError(WEKNORA_IMPORT_ERROR)

        self.base_url = base_url.rstrip("/")
        # Configuration setup
        self.config = Configuration(host=self.base_url)
        if api_key:
            # Assume Bearer token if api_key is provided
            self.config.api_key["BearerAuth"] = api_key
        
        self.api_client = ApiClient(self.config)
        self.logger = logging.getLogger("WeKnoraClient")
        
        # Initialize APIs
        self.knowledge_api = KnowledgeApi(self.api_client)
        self.default_api = DefaultApi(self.api_client)

    def check_connection(self) -> bool:
        """Verify if WeKnora is accessible."""
        try:
            # Using system info or similar as health check
            self.default_api.system_info_get()
            return True
        except Exception as e:
            self.logger.error(f"Connection check failed: {e}")
            return False

    def list_knowledge_bases(self):
        """List all knowledge bases."""
        try:
            return self.knowledge_api.knowledge_bases_get()
        except Exception as e:
            self.logger.error(f"Failed to list knowledge bases: {e}")
            raise
