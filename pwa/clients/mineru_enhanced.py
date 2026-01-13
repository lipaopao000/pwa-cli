"""
Enhanced Mineru API client with full API v4 support
Based on official API documentation: https://mineru.net/apiManage/docs
"""

import hashlib
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Constants
MINERU_API_BASE_URL = "https://mineru.net/api/v4"
MINERU_MODEL_VERSION = "vlm"

# Error code mappings
ERROR_CODES = {
    "A0202": "Token 错误",
    "A0211": "Token 过期",
    "-500": "传参错误",
    "-10001": "服务异常",
    "-10002": "请求参数错误",
    "-60001": "生成上传 URL 失败",
    "-60002": "获取匹配的文件格式失败",
    "-60003": "文件读取失败",
    "-60004": "空文件",
    "-60005": "文件大小超出限制",
    "-60006": "文件页数超过限制",
    "-60007": "模型服务暂时不可用",
    "-60008": "文件读取超时",
    "-60009": "任务提交队列已满",
    "-60010": "解析失败",
    "-60011": "获取有效文件失败",
    "-60012": "找不到任务",
    "-60013": "没有权限访问该任务",
    "-60014": "删除运行中的任务",
    "-60015": "文件转换失败",
    "-60016": "文件转换失败",
    "-60017": "重试次数达到上线",
    "-60018": "每日解析任务数量已达上限",
    "-60019": "html文件解析额度不足",
    "-60020": "文件拆分失败",
    "-60021": "读取文件页数失败",
    "-60022": "网页读取失败",
}


class MineruAPIError(Exception):
    """MinerU API error"""

    def __init__(self, code: str, message: str):
        self.code = code
        self.message = message
        super().__init__(f"[{code}] {message}")


@dataclass
class MineruClientConfig:
    """Configuration for Mineru API client"""

    token: str
    base_url: str = MINERU_API_BASE_URL
    model_version: str = MINERU_MODEL_VERSION
    timeout: int = 30
    max_retries: int = 3
    backoff_factor: float = 0.5
    retry_statuses: Tuple[int, ...] = (500, 502, 503, 504)
    cache_ttl: int = 300
    pool_connections: int = 10
    pool_maxsize: int = 20

    def __post_init__(self):
        if not self.token:
            raise ValueError("Mineru API token is required")


@dataclass
class TaskOptions:
    """Options for creating parsing tasks"""

    # Common options
    is_ocr: bool = False
    enable_formula: bool = True
    enable_table: bool = True
    language: str = "ch"
    data_id: Optional[str] = None
    callback: Optional[str] = None
    seed: Optional[str] = None
    extra_formats: Optional[List[str]] = None
    page_ranges: Optional[str] = None
    model_version: str = MINERU_MODEL_VERSION

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API request"""
        result = {
            "is_ocr": self.is_ocr,
            "enable_formula": self.enable_formula,
            "enable_table": self.enable_table,
            "language": self.language,
            "model_version": self.model_version,
        }

        if self.data_id:
            result["data_id"] = self.data_id
        if self.callback:
            result["callback"] = self.callback
        if self.seed:
            result["seed"] = self.seed
        if self.extra_formats:
            result["extra_formats"] = self.extra_formats
        if self.page_ranges:
            result["page_ranges"] = self.page_ranges

        return result


class SimpleCache:
    """Simple in-memory cache with TTL"""

    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self.default_ttl = default_ttl

    def _generate_key(self, method: str, endpoint: str, **kwargs) -> str:
        """Generate cache key"""
        import json

        key_data = f"{method}:{endpoint}:{json.dumps(kwargs, sort_keys=True)}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        """Get cached value"""
        if key in self._cache:
            value, expire_time = self._cache[key]
            if datetime.now() < expire_time:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set cached value"""
        ttl = ttl or self.default_ttl
        expire_time = datetime.now() + timedelta(seconds=ttl)
        self._cache[key] = (value, expire_time)

    def invalidate(self, key: str):
        """Invalidate cached value"""
        self._cache.pop(key, None)

    def clear(self):
        """Clear all cached values"""
        self._cache.clear()


class MineruEnhancedClient:
    """Enhanced client for Mineru API with full v4 support"""

    def __init__(self, token: str, enable_cache: bool = True, **kwargs):
        """
        Initialize Mineru client

        Args:
            token: API token
            enable_cache: Enable response caching
            **kwargs: Additional config parameters
        """
        self.config = MineruClientConfig(token=token, **kwargs)
        self._session = self._create_session()
        self._cache = SimpleCache(self.config.cache_ttl) if enable_cache else None
        self.logger = logging.getLogger(__name__)

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.backoff_factor,
            status_forcelist=list(self.config.retry_statuses),
            allowed_methods=["GET", "POST", "PUT", "DELETE"],
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=self.config.pool_connections,
            pool_maxsize=self.config.pool_maxsize,
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update(
            {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.config.token}",
            }
        )
        return session

    def _request(self, method: str, endpoint: str, use_cache: bool = True, **kwargs) -> Dict:
        """
        Make API request

        Args:
            method: HTTP method
            endpoint: API endpoint
            use_cache: Use cache for GET requests
            **kwargs: Additional request parameters

        Returns:
            Response data

        Raises:
            MineruAPIError: If API returns error
        """
        url = f"{self.config.base_url}/{endpoint}"
        cache_key = None

        if self._cache and use_cache and method.upper() == "GET":
            cache_key = self._cache._generate_key(method, endpoint, **kwargs)
            cached = self._cache.get(cache_key)
            if cached:
                return cached

        try:
            res = self._session.request(method, url, timeout=self.config.timeout, **kwargs)
            res.raise_for_status()
            result = res.json()

            # Check API error code
            if result.get("code") != 0:
                code = str(result.get("code"))
                msg = result.get("msg", ERROR_CODES.get(code, "Unknown error"))
                raise MineruAPIError(code, msg)

            if cache_key and result:
                self._cache.set(cache_key, result)

            return result
        except requests.exceptions.RequestException as e:
            self.logger.error(f"[Mineru API] {method} {endpoint} failed: {e}")
            raise
        except MineruAPIError:
            raise
        except Exception as e:
            self.logger.error(f"[Mineru API] Unexpected error: {e}")
            raise

    # ========== Single File Parsing ==========

    def create_task(self, url: str, options: Optional[TaskOptions] = None) -> str:
        """
        Create single file parsing task

        Args:
            url: File URL
            options: Task options

        Returns:
            Task ID

        Raises:
            MineruAPIError: If API returns error
        """
        options = options or TaskOptions()
        data = {"url": url, **options.to_dict()}

        resp = self._request("POST", "extract/task", json=data, use_cache=False)
        return resp["data"]["task_id"]

    def get_task_result(self, task_id: str) -> Dict:
        """
        Get single task result

        Args:
            task_id: Task ID

        Returns:
            Task result dict with keys:
                - task_id: Task ID
                - data_id: Data ID (if provided)
                - state: Task state (done/pending/running/failed/converting)
                - full_zip_url: Result ZIP URL (when done)
                - err_msg: Error message (when failed)
                - extract_progress: Progress info (when running)

        Raises:
            MineruAPIError: If API returns error
        """
        resp = self._request("GET", f"extract/task/{task_id}")
        return resp["data"]

    # ========== Batch File Parsing ==========

    def request_batch_upload_urls(
        self, files: List[Dict[str, Any]], options: Optional[TaskOptions] = None
    ) -> Tuple[str, List[str]]:
        """
        Request batch upload URLs for local files

        Args:
            files: List of file info dicts with keys:
                - name: File name (required)
                - data_id: Data ID (optional)
                - is_ocr: Enable OCR (optional)
                - page_ranges: Page ranges (optional)
            options: Common task options (applied to all files)

        Returns:
            Tuple of (batch_id, upload_urls)

        Raises:
            MineruAPIError: If API returns error
        """
        options = options or TaskOptions()
        data = {"files": files, **options.to_dict()}

        resp = self._request("POST", "file-urls/batch", json=data, use_cache=False)
        return resp["data"]["batch_id"], resp["data"]["file_urls"]

    def upload_file(self, upload_url: str, file_path: str) -> bool:
        """
        Upload file to pre-signed URL

        Args:
            upload_url: Pre-signed upload URL
            file_path: Local file path

        Returns:
            True if successful

        Raises:
            Exception: If upload fails
        """
        try:
            with open(file_path, "rb") as f:
                resp = requests.put(upload_url, data=f, timeout=self.config.timeout)
                resp.raise_for_status()
            return True
        except Exception as e:
            self.logger.error(f"Upload failed: {e}")
            raise

    def create_batch_url_tasks(
        self, files: List[Dict[str, Any]], options: Optional[TaskOptions] = None
    ) -> str:
        """
        Create batch parsing tasks from URLs

        Args:
            files: List of file info dicts with keys:
                - url: File URL (required)
                - data_id: Data ID (optional)
                - is_ocr: Enable OCR (optional)
                - page_ranges: Page ranges (optional)
            options: Common task options (applied to all files)

        Returns:
            Batch ID

        Raises:
            MineruAPIError: If API returns error
        """
        options = options or TaskOptions()
        data = {"files": files, **options.to_dict()}

        resp = self._request("POST", "extract/task/batch", json=data, use_cache=False)
        return resp["data"]["batch_id"]

    def get_batch_results(self, batch_id: str) -> List[Dict]:
        """
        Get batch processing results

        Args:
            batch_id: Batch ID

        Returns:
            List of result dicts with keys:
                - file_name: File name
                - state: Task state
                - full_zip_url: Result ZIP URL (when done)
                - err_msg: Error message (when failed)
                - data_id: Data ID (if provided)
                - extract_progress: Progress info (when running)

        Raises:
            MineruAPIError: If API returns error
        """
        resp = self._request("GET", f"extract-results/batch/{batch_id}")
        return resp["data"]["extract_result"]

    # ========== Helper Methods ==========

    def download_result(self, download_url: str) -> bytes:
        """
        Download result ZIP file

        Args:
            download_url: URL to download from

        Returns:
            ZIP file bytes

        Raises:
            Exception: If download fails
        """
        try:
            resp = requests.get(download_url, timeout=self.config.timeout)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            raise

    def wait_for_task(self, task_id: str, poll_interval: int = 5, max_wait: int = 600) -> Dict:
        """
        Wait for task to complete

        Args:
            task_id: Task ID
            poll_interval: Polling interval in seconds
            max_wait: Maximum wait time in seconds

        Returns:
            Final task result

        Raises:
            TimeoutError: If task doesn't complete within max_wait
            MineruAPIError: If task fails
        """
        import time

        start_time = time.time()

        while True:
            result = self.get_task_result(task_id)
            state = result["state"]

            if state == "done":
                return result
            elif state == "failed":
                raise MineruAPIError("-60010", result.get("err_msg", "解析失败"))
            elif time.time() - start_time > max_wait:
                raise TimeoutError(f"Task {task_id} timeout after {max_wait}s")

            time.sleep(poll_interval)

    def wait_for_batch(
        self, batch_id: str, poll_interval: int = 10, max_wait: int = 1800
    ) -> List[Dict]:
        """
        Wait for batch tasks to complete

        Args:
            batch_id: Batch ID
            poll_interval: Polling interval in seconds
            max_wait: Maximum wait time in seconds

        Returns:
            Final batch results

        Raises:
            TimeoutError: If tasks don't complete within max_wait
        """
        import time

        start_time = time.time()

        while True:
            results = self.get_batch_results(batch_id)

            # Check if all tasks are done or failed
            all_done = all(r["state"] in ("done", "failed") for r in results)

            if all_done:
                return results
            elif time.time() - start_time > max_wait:
                raise TimeoutError(f"Batch {batch_id} timeout after {max_wait}s")

            time.sleep(poll_interval)

    def get_error_message(self, code: str) -> str:
        """Get error message for error code"""
        return ERROR_CODES.get(code, "Unknown error")
