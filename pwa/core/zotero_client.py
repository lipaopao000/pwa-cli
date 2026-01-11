# -*- coding: utf-8 -*-
"""
zotero_client.py

Client for interacting with Zotero API (local or remote) to fetch references.
"""

import sys
import os
import urllib.request
import urllib.parse
import ssl
from typing import Optional, Tuple, Any

from .utils import load_yaml_config, Colors

class ZoteroClient:
    """
    A simple client to fetch references from Zotero.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the ZoteroClient.
        
        Args:
            config_path: Path to the zotero_config.yaml file.
        """
        self.config = self._load_config(config_path)

    def _load_config(self, config_path: Optional[str] = None) -> Optional[Any]:
        """Loads Zotero configuration."""
        # Try provided path
        if config_path:
            cfg = load_yaml_config(config_path)
            if cfg: return cfg
            
        # Try current working directory
        cwd_config = os.path.join(os.getcwd(), 'zotero_config.yaml')
        return load_yaml_config(cwd_config)

    def _http_get(self, url: str, timeout: int = 15) -> Optional[str]:
        """Performs a simple HTTP GET request."""
        try:
            ctx = ssl.create_default_context()
            encoded_url = urllib.parse.quote(url, safe=":/?=&%+-.")
            req = urllib.request.Request(encoded_url, headers={
                'User-Agent': 'ZoteroClient/1.0 (Python)'
            })
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                data = resp.read()
                try:
                    return data.decode('utf-8')
                except UnicodeDecodeError:
                    return data.decode('latin-1')
        except Exception as e:
            print(f"{Colors.YELLOW}[ZoteroClient] HTTP GET failed ({url}): {e}{Colors.RESET}", file=sys.stderr)
            return None

    def fetch_biblatex(self) -> Optional[str]:
        """Fetches BibLaTeX content if API is enabled."""
        if not self.config:
            return None
        
        zcfg = self.config.get('zotero') or self.config
        if not zcfg.get('api_enabled'):
            return None
            
        bib_url = zcfg.get('bibtex_url') or zcfg.get('bib_url')
        if not bib_url:
            return None
            
        return self._http_get(bib_url)

    def fetch_csljson(self) -> Optional[str]:
        """Fetches CSL JSON content if API is enabled."""
        if not self.config:
            return None
            
        zcfg = self.config.get('zotero') or self.config
        if not zcfg.get('api_enabled'):
            return None
            
        json_url = zcfg.get('csl_json_url') or zcfg.get('csljson_url')
        if not json_url:
            return None
            
        return self._http_get(json_url)

def fetch_preferred_references(local_ref_path: Optional[str] = None, zotero_config_path: Optional[str] = None) -> Tuple[Optional[str], Optional[str]]:
    """
    Strategy function:
    1. Try Zotero BibLaTeX API (contains 'file' field).
    2. Try Zotero CSL JSON API.
    3. Fallback to local file if provided.

    Returns:
        (content, type) where type is 'biblatex', 'csljson', or None.
    """
    client = ZoteroClient(zotero_config_path)
    
    # 1. Try BibLaTeX via API
    content = client.fetch_biblatex()
    if content:
        return content, 'biblatex'
        
    # 2. Try CSL JSON via API
    content = client.fetch_csljson()
    if content:
        return content, 'csljson'
        
    # 3. Fallback to local file
    if local_ref_path and os.path.exists(local_ref_path):
        ext = os.path.splitext(local_ref_path)[1].lower()
        try:
            with open(local_ref_path, 'r', encoding='utf-8') as f:
                txt = f.read()
            if ext in ['.bib', '.biblatex']:
                return txt, 'biblatex'
            elif ext in ['.json', '.csljson']:
                return txt, 'csljson'
            else:
                return txt, ext.lstrip('.')
        except Exception as e:
            print(f"{Colors.RED}[ZoteroClient] Failed to read local file: {e}{Colors.RESET}", file=sys.stderr)

    return None, None
