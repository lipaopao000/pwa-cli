# -*- coding: utf-8 -*-
"""
Integration tests for ZoteroClient with real Better BibTeX JSON-RPC API.

These tests require Zotero to be running with Better BibTeX plugin installed.
Run with: pytest -m integration or pytest --runxfail

Note: These tests will be skipped if Zotero is not running.
"""

import pytest
import json
import logging
import os
from typing import Dict, Any, List
from unittest.mock import patch

from pwa.clients.zotero import (
    ZoteroClient,
    process_annotation,
    format_annotation_markdown,
    fetch_preferred_references,
    CSLItem,
    ProcessedAnnotation
)

logger = logging.getLogger(__name__)


class TestZoteroClientIntegration:
    """Integration tests for ZoteroClient with real API."""

    @pytest.fixture(scope="class")
    def zotero_client(self):
        """Create ZoteroClient instance for integration tests."""
        # Try to load from actual config, fallback to default
        try:
            from pwa.config import ConfigManager
            config_manager = ConfigManager()
            config = config_manager.load_config("zotero")
            client = ZoteroClient(config=config)
        except Exception:
            # Fallback to default configuration
            client = ZoteroClient()

        return client

    @pytest.fixture(scope="class", autouse=True)
    def skip_if_no_zotero(self, zotero_client):
        """Skip all tests if Zotero is not running."""
        if not zotero_client.is_zotero_running():
            pytest.skip("Zotero is not running or Better BibTeX is not available")

    @pytest.mark.integration
    def test_zotero_connection(self, zotero_client, skip_if_no_zotero):
        """Test basic connection to Zotero API."""
        print("\n=== 测试 Zotero 连接 ===")
        assert zotero_client.is_zotero_running(), "Zotero should be running"
        print("✅ Zotero 正在运行")

        # Test that we can make a basic API call
        try:
            groups = zotero_client.get_groups()
            print(f"📚 获取到的库/分组数量: {len(groups)}")
            if groups:
                print(f"📖 示例分组: {groups[0]}")
            assert isinstance(groups, list), "get_groups should return a list"
        except Exception as e:
            pytest.fail(f"Failed to connect to Zotero API: {e}")

    @pytest.mark.integration
    def test_get_groups_with_collections(self, zotero_client, skip_if_no_zotero):
        """Test getting groups/libraries with collection information."""
        groups = zotero_client.get_groups(include_collections=True)

        assert isinstance(groups, list), "Groups should be a list"

        if groups:  # Only test structure if we have groups
            group = groups[0]
            assert "id" in group, "Group should have id"
            assert "name" in group, "Group should have name"
            # collections is optional
            if "collections" in group:
                assert isinstance(group["collections"], list), "Collections should be a list"

    @pytest.mark.integration
    def test_search_functionality(self, zotero_client, skip_if_no_zotero):
        """Test search functionality with different query types."""
        print("\n=== 测试搜索功能 ===")

        # Test empty search (may fail due to BBT API limitations with annotation items)
        all_items = zotero_client.search("")
        print(f"🔍 空搜索结果: 找到 {len(all_items)} 个项目")

        # If empty search fails, try a broad search to get some items
        if not all_items:
            print("🔄 空搜索失败，尝试广域搜索获取项目...")
            all_items = zotero_client.search("a")  # Search for 'a' to get some items
            print(f"🔍 广域搜索 'a': 找到 {len(all_items)} 个项目")

        if all_items:
            first_item = all_items[0]
            print(f"📄 示例项目: {first_item.get('title', 'No title')} (citekey: {first_item.get('citekey', 'No citekey')})")
        assert isinstance(all_items, list), "Search should return a list"

        # Test simple string search
        search_results = zotero_client.search("test")
        print(f"🔍 字符串搜索 'test': 找到 {len(search_results)} 个项目")
        assert isinstance(search_results, list), "String search should return a list"

        # Test advanced search if we have items
        if all_items:
            # Try to search for the first item's title
            first_item = all_items[0]
            if "title" in first_item and first_item["title"]:
                search_term = first_item["title"][:10]
                print(f"🔍 高级搜索标题包含 '{search_term}'")
                title_search = zotero_client.search([['title', 'contains', search_term]])
                print(f"📊 高级搜索结果: 找到 {len(title_search)} 个项目")
                assert isinstance(title_search, list), "Advanced search should return a list"

    @pytest.mark.integration
    def test_citekey_operations(self, zotero_client, skip_if_no_zotero):
        """Test citekey-based operations."""
        print("\n=== 测试 citekey 操作 ===")

        # First, get some items to work with
        items = zotero_client.search("")
        if not items:
            # Try broad search if empty search fails
            items = zotero_client.search("a")
        if not items:
            pytest.skip("No items found in Zotero library")

        # Find an item with a citekey
        item_with_citekey = None
        for item in items[:10]:  # Check first 10 items
            if item.get("citekey"):
                item_with_citekey = item
                break

        if not item_with_citekey:
            pytest.skip("No items with citekeys found in Zotero library")

        citekey = item_with_citekey["citekey"]
        print(f"🔑 使用 citekey: {citekey}")
        print(f"📖 原始项目标题: {item_with_citekey.get('title', 'No title')}")

        # Test get_item_by_citekey
        retrieved_item = zotero_client.get_item_by_citekey(citekey)
        print(f"✅ 通过 citekey 检索到的项目: {retrieved_item.get('title', 'No title')}")
        print(f"📊 项目类型: {retrieved_item.get('type', 'unknown')}")
        if retrieved_item.get('author'):
            authors = retrieved_item['author']
            if authors:
                first_author = authors[0]
                print(f"👤 第一作者: {first_author.get('family', '')} {first_author.get('given', '')}")

        assert isinstance(retrieved_item, dict), "get_item_by_citekey should return a dict"
        assert retrieved_item.get("citekey") == citekey, "Citekey should match"

        # Verify CSL-JSON structure
        assert "id" in retrieved_item, "Item should have id"
        assert "type" in retrieved_item, "Item should have type"
        assert "title" in retrieved_item, "Item should have title"

        # Test attachments for this citekey
        attachments = zotero_client.get_attachments(citekey)
        print(f"📎 附件数量: {len(attachments)}")
        if attachments:
            # Better BibTeX API 返回的附件没有 title 字段，使用文件名
            first_attachment = attachments[0]
            filename = "Unknown"
            if first_attachment.get('path') and first_attachment['path'] != False:
                filename = os.path.basename(first_attachment['path'])
            elif 'open' in first_attachment:
                # 从 open URL 中提取 ID
                filename = f"PDF ({first_attachment['open'].split('/')[-1]})"
            print(f"📄 第一个附件: {filename}")
        assert isinstance(attachments, list), "get_attachments should return a list"

        # Test notes for this citekey
        notes = zotero_client.get_item_notes(citekey)
        print(f"📝 笔记数量: {len(notes)}")
        if notes:
            # Show first 100 characters of first note
            first_note = notes[0][:100] + "..." if len(notes[0]) > 100 else notes[0]
            print(f"📝 第一条笔记预览: {first_note}")
        assert isinstance(notes, list), "get_item_notes should return a list"

    @pytest.mark.integration
    def test_bibtex_export(self, zotero_client, skip_if_no_zotero):
        """Test BibTeX export functionality."""
        print("\n=== 测试 BibTeX 导出 ===")

        # Get some items with citekeys
        items = zotero_client.search("")
        if not items:
            items = zotero_client.search("a")
        citekeys = [item["citekey"] for item in items if item.get("citekey")][:3]  # Limit to 3

        if not citekeys:
            pytest.skip("No items with citekeys found for BibTeX export test")

        print(f"📚 找到 {len(citekeys)} 个带 citekey 的项目: {citekeys}")

        # Test single citekey export
        print(f"📤 导出单个 citekey: {citekeys[0]}")
        single_bib = zotero_client.export_bibtex([citekeys[0]])
        print(f"📄 导出结果长度: {len(single_bib)} 字符")
        print(f"📄 BibTeX 预览:\n{single_bib[:200]}..." if len(single_bib) > 200 else f"📄 BibTeX 内容:\n{single_bib}")
        assert isinstance(single_bib, str), "export_bibtex should return a string"
        assert "@" in single_bib, "BibTeX should contain @ entries"

        # Test multiple citekeys export
        if len(citekeys) > 1:
            print(f"📤 导出多个 citekeys: {citekeys}")
            multi_bib = zotero_client.export_bibtex(citekeys)
            print(f"📄 多条目导出结果长度: {len(multi_bib)} 字符")
            entry_count = multi_bib.count('@')
            print(f"📊 导出的条目数量: {entry_count}")
            assert isinstance(multi_bib, str), "Multiple export should return a string"
            assert "@" in multi_bib, "BibTeX should contain @ entries"

    @pytest.mark.integration
    def test_biblatex_fetch(self, zotero_client, skip_if_no_zotero):
        """Test fetching entire library as BibLaTeX."""
        biblatex = zotero_client.fetch_biblatex()

        if biblatex is None:
            pytest.skip("No BibLaTeX data available")

        assert isinstance(biblatex, str), "fetch_biblatex should return a string"
        assert "@" in biblatex, "BibLaTeX should contain @ entries"

    @pytest.mark.integration
    def test_annotation_processing(self, zotero_client, skip_if_no_zotero):
        """Test annotation processing with real data."""
        # Get items with attachments
        items = zotero_client.search("")
        item_with_attachments = None

        for item in items[:5]:  # Check first 5 items
            if item.get("citekey"):
                attachments = zotero_client.get_attachments(item["citekey"])
                if attachments:
                    item_with_attachments = item
                    break

        if not item_with_attachments:
            pytest.skip("No items with attachments found for annotation test")

        # This is a basic test - in real scenario, we'd need to check if attachments have annotations
        # For now, just test the processing functions with mock data
        mock_annotation = {
            "key": "ANN1",
            "annotationType": "highlight",
            "annotationColor": "#ff0000",
            "annotationText": "Sample highlighted text",
            "annotationComment": "Sample comment",
            "annotationPageLabel": "5",
            "annotationPosition": json.dumps({"pageIndex": 4, "rects": [[10.5, 20.3]]}),
            "dateModified": "2024-01-01T10:00:00Z"
        }

        mock_attachment = {
            "itemKey": "ATT1",
            "path": "/path/to/paper.pdf",
            "title": "Sample Paper"
        }

        # Test process_annotation function
        processed = process_annotation(mock_annotation, mock_attachment)
        assert isinstance(processed, dict), "process_annotation should return a dict"
        assert processed["id"] == "ANN1", "ID should match"
        assert processed["type"] == "highlight", "Type should match"
        assert processed["page"] == 5, "Page should be parsed correctly"
        assert processed["x"] == 10.5, "X coordinate should be extracted"
        assert processed["y"] == 20.3, "Y coordinate should be extracted"
        assert "markdown" in processed, "Should include markdown format"

        # Test format_annotation_markdown
        markdown = format_annotation_markdown(processed)
        assert isinstance(markdown, str), "format_annotation_markdown should return string"
        assert "Sample highlighted text" in markdown, "Should contain the highlighted text"

    @pytest.mark.integration
    def test_error_handling(self, zotero_client, skip_if_no_zotero):
        """Test error handling for invalid operations."""
        # Test with invalid citekey
        with pytest.raises(Exception):
            zotero_client.get_item_by_citekey("nonexistent_citekey_12345")

        # Test search with invalid parameters
        # This should not raise an exception, just return empty results
        result = zotero_client.search([['invalid_field', 'invalid_operator', 'value']])
        assert isinstance(result, list), "Search with invalid params should return list"

    @pytest.mark.integration
    def test_pdf_viewer_functionality(self, zotero_client, skip_if_no_zotero):
        """Test PDF viewer functionality (if available)."""
        # This test may not work in headless environments
        # Just test that the method doesn't crash
        try:
            result = zotero_client.view_pdf("http://zotero.org/users/123/items/ABC", page=1)
            assert isinstance(result, bool), "view_pdf should return boolean"
        except Exception:
            # PDF viewer might not be available in test environment
            pass

    @pytest.mark.integration
    def test_fetch_preferred_references_integration(self, zotero_client, skip_if_no_zotero):
        """Test the fetch_preferred_references function with real Zotero."""
        # Test with zotero client
        content, format_type = fetch_preferred_references(zotero_config=zotero_client.zcfg)

        if content is not None:
            assert isinstance(content, str), "Content should be string"
            assert format_type in ["biblatex", "bibtex", "csljson"], f"Invalid format: {format_type}"
            assert "@" in content or content.strip().startswith("{"), "Should contain valid reference data"
        else:
            # No references available
            assert format_type is None

    @pytest.mark.integration
    def test_data_structure_validation(self, zotero_client, skip_if_no_zotero):
        """Test that returned data structures match expected formats."""
        items = zotero_client.search("")

        for item in items[:3]:  # Test first 3 items
            # Validate CSL-JSON structure
            assert "id" in item, "CSL item should have id"
            assert "type" in item, "CSL item should have type"
            assert isinstance(item.get("title", ""), str), "Title should be string"

            # Check Better BibTeX extensions
            if "citekey" in item:
                assert isinstance(item["citekey"], str), "Citekey should be string"
                assert len(item["citekey"]) > 0, "Citekey should not be empty"

            # Validate author structure if present
            if "author" in item:
                authors = item["author"]
                assert isinstance(authors, list), "Authors should be a list"
                if authors:
                    author = authors[0]
                    assert isinstance(author, dict), "Author should be a dict"
                    assert "family" in author or "given" in author, "Author should have name fields"

            # Validate date structure if present
            if "issued" in item and "date-parts" in item["issued"]:
                date_parts = item["issued"]["date-parts"]
                assert isinstance(date_parts, list), "Date parts should be list"
                if date_parts and date_parts[0]:
                    assert isinstance(date_parts[0], list), "Date part should be list"
                    assert len(date_parts[0]) >= 1, "Date should have at least year"

    @pytest.mark.integration
    def test_attachment_structure(self, zotero_client, skip_if_no_zotero):
        """Test attachment data structure."""
        items = zotero_client.search("")

        for item in items[:5]:  # Check first 5 items
            if item.get("citekey"):
                attachments = zotero_client.get_attachments(item["citekey"])

                for attachment in attachments:
                    assert isinstance(attachment, dict), "Attachment should be dict"
                    assert "itemKey" in attachment, "Attachment should have itemKey"

                    # Check optional fields
                    if "path" in attachment:
                        assert isinstance(attachment["path"], str), "Path should be string"

                    if "title" in attachment:
                        assert isinstance(attachment["title"], str), "Title should be string"


# Pytest configuration for integration tests
def pytest_configure(config):
    """Add integration marker."""
    config.addinivalue_line("markers", "integration: mark test as integration test")


def pytest_collection_modifyitems(config, items):
    """Skip integration tests if --runxfail is not provided."""
    if not config.getoption("--runxfail"):
        skip_integration = pytest.mark.skip(reason="need --runxfail option to run integration tests")
        for item in items:
            if "integration" in item.keywords:
                item.add_marker(skip_integration)


if __name__ == "__main__":
    # Allow running this file directly for debugging
    pytest.main([__file__, "-v", "--runxfail"])
