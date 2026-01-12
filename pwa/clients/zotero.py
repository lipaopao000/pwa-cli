# -*- coding: utf-8 -*-
"""
zotero_client.py

Client for interacting with Zotero API (local or remote) to fetch references.
"""

import logging
import os
import ssl
import urllib.parse
import urllib.request
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class ZoteroClient:
    """
    A simple client to fetch references from Zotero.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """
        Initialize the ZoteroClient.

        Args:
            config: Zotero configuration dictionary (preferred).
            config_path: Path to the zotero_config.yaml file (fallback).
        """
        self.config = config or self._load_config(config_path)

    def _load_config(self, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Loads Zotero configuration.

        Args:
            config_path: Path to the zotero_config.yaml file.

        Returns:
            Configuration dictionary or None.
        """
        # Try to use ConfigManager if available
        try:
            from ..config import ConfigManager

            config_manager = ConfigManager()
            return config_manager.get_config("zotero")
        except Exception as e:
            logger.warning(f"ConfigManager not available, trying direct path: {e}")

        # Fallback to direct file loading
        if config_path and os.path.exists(config_path):
            try:
                import yaml

                with open(config_path, "r", encoding="utf-8") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                logger.error(f"Failed to load config from {config_path}: {e}")

        return None

    def _http_get(self, url: str, timeout: int = 15) -> Optional[str]:
        """
        Performs a simple HTTP GET request.

        Args:
            url: URL to fetch.
            timeout: Request timeout in seconds.

        Returns:
            Response content as string or None on error.
        """
        try:
            ctx = ssl.create_default_context()
            encoded_url = urllib.parse.quote(url, safe=":/?=&%+-.")
            req = urllib.request.Request(
                encoded_url, headers={"User-Agent": "PWA-CLI ZoteroClient/1.0 (Python)"}
            )
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                data = resp.read()
                try:
                    return data.decode("utf-8")
                except UnicodeDecodeError:
                    return data.decode("latin-1")
        except Exception as e:
            logger.warning(f"HTTP GET failed ({url}): {e}")
            return None

    def fetch_biblatex(self) -> Optional[str]:
        """
        Fetches BibLaTeX content if API is enabled.

        Returns:
            BibLaTeX content as string or None.
        """
        if not self.config:
            logger.warning("No Zotero configuration available")
            return None

        zcfg = self.config.get("zotero") or self.config
        if not zcfg.get("api_enabled"):
            logger.info("Zotero API is not enabled")
            return None

        bib_url = zcfg.get("bibtex_url") or zcfg.get("bib_url")
        if not bib_url:
            logger.warning("No BibTeX URL configured")
            return None

        logger.info(f"Fetching BibLaTeX from Zotero API: {bib_url}")
        return self._http_get(bib_url)

    def fetch_csljson(self) -> Optional[str]:
        """
        Fetches CSL JSON content if API is enabled.

        Returns:
            CSL JSON content as string or None.
        """
        if not self.config:
            logger.warning("No Zotero configuration available")
            return None

        zcfg = self.config.get("zotero") or self.config
        if not zcfg.get("api_enabled"):
            logger.info("Zotero API is not enabled")
            return None

        json_url = zcfg.get("csl_json_url") or zcfg.get("csljson_url")
        if not json_url:
            logger.warning("No CSL JSON URL configured")
            return None

        logger.info(f"Fetching CSL JSON from Zotero API: {json_url}")
        return self._http_get(json_url)


def fetch_preferred_references(
    local_ref_path: Optional[str] = None,
    zotero_config: Optional[Dict[str, Any]] = None,
    zotero_config_path: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """
    Strategy function to fetch references from multiple sources.

    Priority:
    1. Try Zotero BibLaTeX API (contains 'file' field).
    2. Try Zotero CSL JSON API.
    3. Fallback to local file if provided.

    Args:
        local_ref_path: Path to local reference file.
        zotero_config: Zotero configuration dictionary.
        zotero_config_path: Path to zotero_config.yaml file.

    Returns:
        (content, type) where type is 'biblatex', 'csljson', or None.
    """
    client = ZoteroClient(config=zotero_config, config_path=zotero_config_path)

    # 1. Try BibLaTeX via API
    content = client.fetch_biblatex()
    if content:
        logger.info("Successfully fetched BibLaTeX from Zotero API")
        return content, "biblatex"

    # 2. Try CSL JSON via API
    content = client.fetch_csljson()
    if content:
        logger.info("Successfully fetched CSL JSON from Zotero API")
        return content, "csljson"

    # 3. Fallback to local file
    if local_ref_path and os.path.exists(local_ref_path):
        ext = os.path.splitext(local_ref_path)[1].lower()
        try:
            with open(local_ref_path, "r", encoding="utf-8") as f:
                txt = f.read()
            if ext in [".bib", ".biblatex"]:
                logger.info(f"Loaded BibLaTeX from local file: {local_ref_path}")
                return txt, "biblatex"
            elif ext in [".json", ".csljson"]:
                logger.info(f"Loaded CSL JSON from local file: {local_ref_path}")
                return txt, "csljson"
            else:
                logger.warning(f"Unknown file extension: {ext}")
                return txt, ext.lstrip(".")
        except Exception as e:
            logger.error(f"Failed to read local file {local_ref_path}: {e}")

    logger.warning("No references could be fetched from any source")
    return None, None
