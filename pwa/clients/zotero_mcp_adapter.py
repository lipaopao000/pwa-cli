"""
Zotero-MCP adapter for PWA-CLI.

This module provides a clean interface to zotero-mcp's core features without
importing the full MCP server infrastructure.
"""

import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add zotero-mcp to path
ZOTERO_MCP_SRC = Path(__file__).parent.parent.parent / ".zotero-mcp" / "src"
if ZOTERO_MCP_SRC.exists() and str(ZOTERO_MCP_SRC) not in sys.path:
    sys.path.insert(0, str(ZOTERO_MCP_SRC))


def _load_module_directly(module_name: str, file_path: Path):
    """Load a Python module directly from file path, bypassing __init__.py."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    raise ImportError(f"Could not load module {module_name} from {file_path}")


# Load core modules directly to avoid __init__.py dependencies
try:
    # Load utils first (no dependencies on other zotero_mcp modules)
    utils_path = ZOTERO_MCP_SRC / "zotero_mcp" / "utils.py"
    utils_module = _load_module_directly("zotero_mcp.utils", utils_path)

    # Load client module
    client_path = ZOTERO_MCP_SRC / "zotero_mcp" / "client.py"
    # Temporarily remove zotero_mcp from sys.modules to avoid __init__.py
    if "zotero_mcp" in sys.modules:
        del sys.modules["zotero_mcp"]
    client_module = _load_module_directly("zotero_mcp.client", client_path)

    # Load better_bibtex_client
    bbt_path = ZOTERO_MCP_SRC / "zotero_mcp" / "better_bibtex_client.py"
    bbt_module = _load_module_directly("zotero_mcp.better_bibtex_client", bbt_path)

    # Load pdfannots modules
    pdfannots_helper_path = ZOTERO_MCP_SRC / "zotero_mcp" / "pdfannots_helper.py"
    pdfannots_helper_module = _load_module_directly(
        "zotero_mcp.pdfannots_helper", pdfannots_helper_path
    )

    pdfannots_downloader_path = ZOTERO_MCP_SRC / "zotero_mcp" / "pdfannots_downloader.py"
    pdfannots_downloader_module = _load_module_directly(
        "zotero_mcp.pdfannots_downloader", pdfannots_downloader_path
    )

except Exception as e:
    raise ImportError(
        f"Failed to load zotero-mcp modules. "
        f"Please run: bash scripts/install_zotero_mcp.sh\n"
        f"Error: {e}"
    )


class ZoteroMCPClient:
    """
    Adapter for zotero-mcp functionality.

    Provides access to:
    - Local Zotero connection
    - PDF annotation extraction
    - Better BibTeX integration
    - Enhanced metadata formatting
    """

    def __init__(
        self,
        library_id: Optional[str] = None,
        library_type: str = "user",
        api_key: Optional[str] = None,
        local: bool = True,
    ):
        """
        Initialize Zotero-MCP client.

        Args:
            library_id: Zotero library ID (defaults to "0" for local mode)
            library_type: Library type ("user" or "group")
            api_key: Zotero API key (not needed for local mode)
            local: Use local Zotero API (default: True)
        """
        # Set environment variables for zotero-mcp
        if local:
            os.environ["ZOTERO_LOCAL"] = "true"
            if not library_id:
                library_id = "0"

        if library_id:
            os.environ["ZOTERO_LIBRARY_ID"] = library_id
        if api_key:
            os.environ["ZOTERO_API_KEY"] = api_key
        if library_type:
            os.environ["ZOTERO_LIBRARY_TYPE"] = library_type

        # Initialize Zotero client
        self.zotero_client = client_module.get_zotero_client()
        self.local = local

    def search_items(
        self,
        query: Optional[str] = None,
        item_type: Optional[str] = None,
        tag: Optional[str] = None,
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        """
        Search for items in Zotero library.

        Args:
            query: Search query string
            item_type: Filter by item type (e.g., "journalArticle")
            tag: Filter by tag
            limit: Maximum number of results

        Returns:
            List of Zotero items
        """
        params = {"limit": limit}

        if query:
            params["q"] = query
        if item_type:
            params["itemType"] = item_type
        if tag:
            params["tag"] = tag

        return self.zotero_client.items(**params)

    def get_item(self, item_key: str) -> Dict[str, Any]:
        """
        Get a single item by key.

        Args:
            item_key: Zotero item key

        Returns:
            Item data
        """
        return self.zotero_client.item(item_key)

    def format_item_metadata(self, item: Dict[str, Any], include_abstract: bool = True) -> str:
        """
        Format item metadata as markdown.

        Args:
            item: Zotero item dictionary
            include_abstract: Include abstract in output

        Returns:
            Markdown-formatted metadata
        """
        return client_module.format_item_metadata(item, include_abstract)

    def get_item_attachments(self, item_key: str) -> List[Dict[str, Any]]:
        """
        Get attachments for an item.

        Args:
            item_key: Zotero item key

        Returns:
            List of attachment items
        """
        return self.zotero_client.children(item_key)

    def get_collections(self) -> List[Dict[str, Any]]:
        """
        Get all collections in the library.

        Returns:
            List of collections
        """
        return self.zotero_client.collections()

    def get_tags(self) -> List[Dict[str, Any]]:
        """
        Get all tags in the library.

        Returns:
            List of tags
        """
        return self.zotero_client.tags()

    def extract_pdf_annotations(
        self, item_key: str, include_images: bool = False
    ) -> Dict[str, Any]:
        """
        Extract annotations from PDF attachments.

        Args:
            item_key: Zotero item key
            include_images: Include image annotations

        Returns:
            Dictionary with annotations data
        """
        try:
            downloader = pdfannots_downloader_module.PDFAnnotsDownloader(self.zotero_client)
            return downloader.extract_annotations(item_key, include_images)
        except Exception as e:
            return {
                "error": str(e),
                "item_key": item_key,
                "annotations": [],
            }

    def get_better_bibtex_export(self, item_keys: List[str], translator: str = "biblatex") -> str:
        """
        Export items using Better BibTeX.

        Args:
            item_keys: List of item keys to export
            translator: Export format ("biblatex", "bibtex", etc.)

        Returns:
            Exported bibliography string
        """
        try:
            bbt_client = bbt_module.BetterBibTeXClient()
            return bbt_client.export_items(item_keys, translator)
        except Exception as e:
            return f"Error: {e}"

    def format_creators(self, creators: List[Dict[str, Any]]) -> str:
        """
        Format creators (authors) list.

        Args:
            creators: List of creator dictionaries

        Returns:
            Formatted string
        """
        return utils_module.format_creators(creators)


def create_zotero_mcp_client(
    local: bool = True,
    library_id: Optional[str] = None,
    api_key: Optional[str] = None,
    library_type: str = "user",
) -> ZoteroMCPClient:
    """
    Create a Zotero-MCP client instance.

    Args:
        local: Use local Zotero API
        library_id: Zotero library ID
        api_key: Zotero API key
        library_type: Library type ("user" or "group")

    Returns:
        Configured ZoteroMCPClient instance
    """
    return ZoteroMCPClient(
        library_id=library_id,
        library_type=library_type,
        api_key=api_key,
        local=local,
    )
