"""
Tests for Mineru API client
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from pwa.clients.mineru import (
    MineruClient,
    MineruClientConfig,
    TaskOptions,
    MineruAPIError,
    ERROR_CODES,
)


class TestMineruClientConfig:
    """Test MineruClientConfig"""

    def test_config_creation(self):
        """Test config creation"""
        config = MineruClientConfig(token="test_token")
        assert config.token == "test_token"
        assert config.model_version == "vlm"
        assert config.timeout == 30

    def test_config_requires_token(self):
        """Test config requires token"""
        with pytest.raises(ValueError, match="token is required"):
            MineruClientConfig(token="")


class TestTaskOptions:
    """Test TaskOptions"""

    def test_default_options(self):
        """Test default options"""
        options = TaskOptions()
        assert options.is_ocr is False
        assert options.enable_formula is True
        assert options.enable_table is True
        assert options.language == "ch"
        assert options.model_version == "vlm"

    def test_to_dict(self):
        """Test to_dict conversion"""
        options = TaskOptions(
            is_ocr=True,
            enable_formula=False,
            data_id="test123",
            extra_formats=["docx", "html"],
        )
        result = options.to_dict()

        assert result["is_ocr"] is True
        assert result["enable_formula"] is False
        assert result["data_id"] == "test123"
        assert result["extra_formats"] == ["docx", "html"]

    def test_to_dict_excludes_none(self):
        """Test to_dict excludes None values"""
        options = TaskOptions()
        result = options.to_dict()

        assert "data_id" not in result
        assert "callback" not in result
        assert "seed" not in result


class TestMineruClient:
    """Test MineruClient"""

    @pytest.fixture
    def client(self):
        """Create test client"""
        return MineruClient(token="test_token")

    @pytest.fixture
    def mock_response(self):
        """Create mock response"""
        mock = Mock()
        mock.status_code = 200
        mock.json.return_value = {
            "code": 0,
            "msg": "ok",
            "data": {"task_id": "test_task_id"},
        }
        return mock

    def test_client_creation(self, client):
        """Test client creation"""
        assert client.config.token == "test_token"
        assert client._session is not None
        assert client._cache is not None

    def test_client_without_cache(self):
        """Test client without cache"""
        client = MineruClient(token="test_token", enable_cache=False)
        assert client._cache is None

    @patch("requests.Session.request")
    def test_create_task(self, mock_request, client, mock_response):
        """Test create_task"""
        mock_request.return_value = mock_response

        task_id = client.create_task("https://example.com/test.pdf")

        assert task_id == "test_task_id"
        mock_request.assert_called_once()

    @patch("requests.Session.request")
    def test_create_task_with_options(self, mock_request, client, mock_response):
        """Test create_task with options"""
        mock_request.return_value = mock_response

        options = TaskOptions(
            is_ocr=True,
            data_id="test123",
            extra_formats=["docx"],
        )
        task_id = client.create_task("https://example.com/test.pdf", options)

        assert task_id == "test_task_id"
        call_args = mock_request.call_args
        assert call_args[1]["json"]["is_ocr"] is True
        assert call_args[1]["json"]["data_id"] == "test123"

    @patch("requests.Session.request")
    def test_get_task_result(self, mock_request, client):
        """Test get_task_result"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "ok",
            "data": {
                "task_id": "test_task_id",
                "state": "done",
                "full_zip_url": "https://example.com/result.zip",
            },
        }
        mock_request.return_value = mock_response

        result = client.get_task_result("test_task_id")

        assert result["task_id"] == "test_task_id"
        assert result["state"] == "done"

    @patch("requests.Session.request")
    def test_api_error_handling(self, mock_request, client):
        """Test API error handling"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": -60005,
            "msg": "文件大小超出限制",
        }
        mock_request.return_value = mock_response

        with pytest.raises(MineruAPIError) as exc_info:
            client.create_task("https://example.com/test.pdf")

        assert exc_info.value.code == "-60005"
        assert "文件大小超出限制" in str(exc_info.value)

    @patch("requests.Session.request")
    def test_request_batch_upload_urls(self, mock_request, client):
        """Test request_batch_upload_urls"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "ok",
            "data": {
                "batch_id": "batch123",
                "file_urls": ["https://example.com/upload1", "https://example.com/upload2"],
            },
        }
        mock_request.return_value = mock_response

        files = [
            {"name": "test1.pdf", "data_id": "id1"},
            {"name": "test2.pdf", "data_id": "id2"},
        ]
        batch_id, urls = client.request_batch_upload_urls(files)

        assert batch_id == "batch123"
        assert len(urls) == 2

    @patch("requests.Session.request")
    def test_create_batch_url_tasks(self, mock_request, client):
        """Test create_batch_url_tasks"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "ok",
            "data": {"batch_id": "batch456"},
        }
        mock_request.return_value = mock_response

        files = [
            {"url": "https://example.com/test1.pdf", "data_id": "id1"},
            {"url": "https://example.com/test2.pdf", "data_id": "id2"},
        ]
        batch_id = client.create_batch_url_tasks(files)

        assert batch_id == "batch456"

    @patch("requests.Session.request")
    def test_get_batch_results(self, mock_request, client):
        """Test get_batch_results"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "code": 0,
            "msg": "ok",
            "data": {
                "batch_id": "batch123",
                "extract_result": [
                    {"file_name": "test1.pdf", "state": "done"},
                    {"file_name": "test2.pdf", "state": "running"},
                ],
            },
        }
        mock_request.return_value = mock_response

        results = client.get_batch_results("batch123")

        assert len(results) == 2
        assert results[0]["state"] == "done"
        assert results[1]["state"] == "running"

    @patch("requests.get")
    def test_download_result(self, mock_get, client):
        """Test download_result"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b"test content"
        mock_get.return_value = mock_response

        content = client.download_result("https://example.com/result.zip")

        assert content == b"test content"

    def test_get_error_message(self, client):
        """Test get_error_message"""
        msg = client.get_error_message("A0202")
        assert msg == "Token 错误"

        msg = client.get_error_message("-60005")
        assert msg == "文件大小超出限制"

        msg = client.get_error_message("unknown")
        assert msg == "Unknown error"


class TestMineruAPIError:
    """Test MineruAPIError"""

    def test_error_creation(self):
        """Test error creation"""
        error = MineruAPIError("-60005", "文件大小超出限制")
        assert error.code == "-60005"
        assert error.message == "文件大小超出限制"
        assert "[-60005]" in str(error)


class TestErrorCodes:
    """Test error codes mapping"""

    def test_error_codes_exist(self):
        """Test error codes exist"""
        assert "A0202" in ERROR_CODES
        assert "-60005" in ERROR_CODES
        assert ERROR_CODES["A0202"] == "Token 错误"
        assert ERROR_CODES["-60005"] == "文件大小超出限制"
