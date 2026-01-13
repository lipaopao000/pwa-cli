"""
Tests for Zotero-MCP adapter.
"""

import pytest

from pwa.clients.zotero_mcp_adapter import ZoteroMCPClient, create_zotero_mcp_client


class TestZoteroMCPClient:
    """Tests for ZoteroMCPClient class."""

    def test_client_creation(self):
        """Test creating a ZoteroMCPClient instance."""
        client = create_zotero_mcp_client(local=True)
        assert isinstance(client, ZoteroMCPClient)
        assert client.local is True

    def test_client_with_api_key(self):
        """Test creating client with API key."""
        client = ZoteroMCPClient(
            library_id="12345",
            library_type="user",
            api_key="test_key",
            local=False,
        )
        assert isinstance(client, ZoteroMCPClient)
        assert client.local is False

    def test_client_methods_exist(self):
        """Test that all expected methods exist."""
        client = create_zotero_mcp_client(local=True)

        assert hasattr(client, "search_items")
        assert hasattr(client, "get_item")
        assert hasattr(client, "format_item_metadata")
        assert hasattr(client, "get_item_attachments")
        assert hasattr(client, "get_collections")
        assert hasattr(client, "get_tags")
        assert hasattr(client, "extract_pdf_annotations")
        assert hasattr(client, "get_better_bibtex_export")
        assert hasattr(client, "format_creators")

    def test_format_creators(self):
        """Test formatting creators list."""
        client = create_zotero_mcp_client(local=True)

        creators = [
            {"creatorType": "author", "firstName": "John", "lastName": "Doe"},
            {"creatorType": "author", "firstName": "Jane", "lastName": "Smith"},
        ]

        result = client.format_creators(creators)
        assert isinstance(result, str)
        assert "Doe" in result or "John" in result


class TestModuleImports:
    """Test that required modules are available."""

    def test_zotero_mcp_modules_loaded(self):
        """Test that zotero-mcp modules are loaded."""
        from pwa.clients import zotero_mcp_adapter

        # Check that modules were loaded
        assert hasattr(zotero_mcp_adapter, "client_module")
        assert hasattr(zotero_mcp_adapter, "utils_module")
        assert hasattr(zotero_mcp_adapter, "bbt_module")
        assert hasattr(zotero_mcp_adapter, "pdfannots_downloader_module")

    def test_create_function(self):
        """Test the create_zotero_mcp_client function."""
        client = create_zotero_mcp_client()
        assert isinstance(client, ZoteroMCPClient)
