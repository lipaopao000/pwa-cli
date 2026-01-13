# -*- coding: utf-8 -*-
import unittest
from unittest.mock import patch, MagicMock
import json
from pwa.clients.zotero import ZoteroClient, process_annotation, format_annotation_markdown

class TestZoteroClient(unittest.TestCase):
    def setUp(self):
        self.config = {
            "zotero": {
                "port": "23119",
                "database": "Zotero"
            }
        }
        self.client = ZoteroClient(config=self.config)

    @patch('requests.get')
    def test_is_zotero_running_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = "ready"
        mock_get.return_value = mock_response
        
        self.assertTrue(self.client.is_zotero_running())
        mock_get.assert_called_once_with(
            f"http://127.0.0.1:23119/better-bibtex/cayw?probe=true",
            headers=self.client.headers,
            timeout=5
        )

    @patch('requests.get')
    def test_is_zotero_running_failure(self, mock_get):
        mock_get.side_effect = Exception("Connection refused")
        self.assertFalse(self.client.is_zotero_running())

    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_get_groups(self, mock_rpc):
        expected_groups = [{"id": 0, "name": "My Library"}]
        mock_rpc.return_value = expected_groups
        
        groups = self.client.get_groups(include_collections=True)
        self.assertEqual(groups, expected_groups)
        mock_rpc.assert_called_with("user.groups", [True])

    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_view_pdf(self, mock_rpc):
        mock_rpc.return_value = {}
        
        result = self.client.view_pdf("http://zotero.org/users/123/items/ABC", page=5)
        self.assertTrue(result)
        mock_rpc.assert_called_with("viewer.viewPDF", ["http://zotero.org/users/123/items/ABC", 5])

    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_search_string(self, mock_rpc):
        mock_rpc.return_value = [{"title": "Zotero"}]
        
        results = self.client.search("Zotero")
        self.assertEqual(len(results), 1)
        mock_rpc.assert_called_with("item.search", ["Zotero"])

    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_search_advanced(self, mock_rpc):
        mock_rpc.return_value = [{"title": "Zotero Paper"}]
        terms = [['title', 'contains', 'Zotero']]
        
        results = self.client.search(terms, library=1)
        self.assertEqual(len(results), 1)
        mock_rpc.assert_called_with("item.search", [terms, 1])

    @patch('requests.post')
    def test_make_rpc_request_success(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "result": {"status": "ok"},
            "id": 1
        }
        mock_post.return_value = mock_response
        
        result = self.client._make_rpc_request("test.method", ["param1"])
        self.assertEqual(result, {"status": "ok"})

    @patch('requests.post')
    def test_make_rpc_request_error(self, mock_post):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "jsonrpc": "2.0",
            "error": {"message": "Method not found", "data": "extra info"},
            "id": 1
        }
        mock_post.return_value = mock_response
        
        with self.assertRaisesRegex(Exception, "API error: Method not found: extra info"):
            self.client._make_rpc_request("test.method", [])

    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_get_item_by_citekey(self, mock_rpc):
        # Mock search result
        mock_rpc.side_effect = [
            [{"citekey": "test2024", "libraryID": 1}], # item.search
            {"items": [{"citekey": "test2024", "title": "Test Title"}]} # item.export
        ]
        
        item = self.client.get_item_by_citekey("test2024")
        self.assertEqual(item["citekey"], "test2024")
        self.assertEqual(item["title"], "Test Title")
        
        self.assertEqual(mock_rpc.call_count, 2)

    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_get_attachments(self, mock_rpc):
        expected_attachments = [{"itemKey": "A1", "path": "/path/to/pdf"}]
        mock_rpc.return_value = expected_attachments
        
        attachments = self.client.get_attachments("test2024")
        self.assertEqual(attachments, expected_attachments)
        mock_rpc.assert_called_with("item.attachments", ["test2024", "*"])

    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_get_item_notes(self, mock_rpc):
        expected_notes = {"test2024": [{"note": "Test Note"}]}
        mock_rpc.return_value = expected_notes
        
        notes = self.client.get_item_notes("test2024")
        self.assertEqual(notes, [{"note": "Test Note"}])

    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_export_bibtex(self, mock_rpc):
        mock_rpc.return_value = "@article{test2024, ...}"
        
        bib = self.client.export_bibtex(["test2024"])
        self.assertEqual(bib, "@article{test2024, ...}")
        
    @patch('pwa.clients.zotero.ZoteroClient._make_rpc_request')
    def test_fetch_biblatex(self, mock_rpc):
        mock_rpc.side_effect = [
            [{"citekey": "key1"}, {"citekey": "key2"}], # item.search
            "@book{key1, ...}\n@article{key2, ...}" # item.export
        ]
        
        bib = self.client.fetch_biblatex()
        self.assertIn("@book{key1", bib)
        self.assertEqual(mock_rpc.call_count, 2)

    def test_process_annotation(self):
        annotation = {
            "key": "ANN1",
            "annotationType": "highlight",
            "annotationColor": "#ff0000",
            "annotationText": "highlighted text",
            "annotationComment": "my comment",
            "annotationPageLabel": "5",
            "annotationPosition": json.dumps({"pageIndex": 4}),
            "dateModified": "2024-01-01"
        }
        attachment = {
            "itemKey": "ATT1",
            "path": "/path/to/paper.pdf",
            "title": "Paper Title"
        }
        
        result = process_annotation(annotation, attachment)
        self.assertEqual(result['id'], "ANN1")
        self.assertEqual(result['page'], 5)
        self.assertEqual(result['annotatedText'], "highlighted text")
        self.assertIn("markdown", result)
        self.assertIn("> \"highlighted text\"", result['markdown'])

    def test_format_annotation_markdown(self):
        annot = {
            "annotatedText": "hello",
            "color": "#ff0000",
            "type": "highlight",
            "pageLabel": "10",
            "comment": "world"
        }
        md = format_annotation_markdown(annot)
        self.assertIn("> \"hello\"", md)
        self.assertIn("(#ff0000)", md)
        self.assertIn("Highlight", md)
        self.assertIn("[Page 10]", md)
        self.assertIn("world", md)

if __name__ == '__main__':
    unittest.main()
