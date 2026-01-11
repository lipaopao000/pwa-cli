"""
Mineru API client for full-text PDF to Markdown conversion
"""

import os
import json
import requests
import hashlib
import zipfile
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime, timedelta
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from concurrent.futures import ThreadPoolExecutor, as_completed

from ..core.utils import parse_biblatex_content
from .zotero import fetch_preferred_references


# Constants
MINERU_API_BASE_URL = "https://mineru.net/api/v4"
MINERU_MODEL_VERSION = "vlm"
TASK_STATUS_FILE = "fulltext_tasks.json"


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


class SimpleCache:
    """Simple in-memory cache with TTL"""
    
    def __init__(self, default_ttl: int = 300):
        self._cache: Dict[str, Tuple[Any, datetime]] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, method: str, endpoint: str, **kwargs) -> str:
        """Generate cache key"""
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


class MineruClient:
    """Client for Mineru OCR API"""
    
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
            allowed_methods=["GET", "POST", "PUT", "DELETE"]
        )
        adapter = HTTPAdapter(
            max_retries=retry,
            pool_connections=self.config.pool_connections,
            pool_maxsize=self.config.pool_maxsize
        )
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config.token}"
        })
        return session
    
    def _request(self, method: str, endpoint: str, use_cache: bool = True, **kwargs) -> Optional[Dict]:
        """
        Make API request
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            use_cache: Use cache for GET requests
            **kwargs: Additional request parameters
            
        Returns:
            Response data or None on error
        """
        url = f"{self.config.base_url}/{endpoint}"
        cache_key = None
        
        if self._cache and use_cache and method.upper() == 'GET':
            cache_key = self._cache._generate_key(method, endpoint, **kwargs)
            cached = self._cache.get(cache_key)
            if cached:
                return cached
        
        try:
            res = self._session.request(method, url, timeout=self.config.timeout, **kwargs)
            res.raise_for_status()
            result = res.json()
            
            if cache_key and result:
                self._cache.set(cache_key, result)
            
            return result
        except Exception as e:
            self.logger.error(f"[Mineru API] {method} {endpoint} failed: {e}")
            return None
    
    def create_task(self, pdf_url: str) -> Optional[str]:
        """
        Create OCR task from PDF URL
        
        Args:
            pdf_url: URL to PDF file
            
        Returns:
            Task ID or None on error
        """
        data = {"url": pdf_url, "model_version": self.config.model_version}
        resp = self._request('POST', 'extract/task', json=data, use_cache=False)
        return resp['data']['task_id'] if resp and resp.get('code') == 0 else None
    
    def request_batch_upload_urls(self, file_infos: List[Dict[str, str]]) -> Tuple[Optional[str], Optional[List[str]]]:
        """
        Request batch upload URLs for local files
        
        Args:
            file_infos: List of file info dicts with 'file_name' and 'citation_key'
            
        Returns:
            Tuple of (batch_id, upload_urls) or (None, None) on error
        """
        files_data = [{"name": info["file_name"], "data_id": info["citation_key"]} for info in file_infos]
        data = {"files": files_data, "model_version": self.config.model_version}
        resp = self._request('POST', 'file-urls/batch', json=data, use_cache=False)
        
        if resp and resp.get('code') == 0:
            return resp['data']['batch_id'], resp['data']['file_urls']
        return None, None
    
    def get_batch_results(self, batch_id: str) -> Optional[List[Dict]]:
        """
        Get batch processing results
        
        Args:
            batch_id: Batch ID
            
        Returns:
            List of result dicts or None on error
        """
        resp = self._request('GET', f'extract-results/batch/{batch_id}')
        return resp.get('data', {}).get('extract_result', []) if resp else None
    
    def get_task_result(self, task_id: str) -> Optional[Dict]:
        """
        Get single task result
        
        Args:
            task_id: Task ID
            
        Returns:
            Result dict or None on error
        """
        resp = self._request('GET', f'extract/task/{task_id}')
        return resp.get('data') if resp else None
    
    def download_result(self, download_url: str) -> Optional[bytes]:
        """
        Download result ZIP file
        
        Args:
            download_url: URL to download from
            
        Returns:
            ZIP file bytes or None on error
        """
        try:
            resp = requests.get(download_url, timeout=self.config.timeout)
            resp.raise_for_status()
            return resp.content
        except Exception as e:
            self.logger.error(f"Download failed: {e}")
            return None


class FullTextProcessor:
    """Processor for full-text PDF to Markdown conversion"""
    
    def __init__(self, output_dir: str = "FullTextMD", config_manager=None):
        """
        Initialize processor
        
        Args:
            output_dir: Output directory for Markdown files
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load API token
        ocr_config = config_manager.load_config('ocr') if config_manager else {}
        token = ocr_config.get('mineru_api_token')
        
        if not token:
            raise ValueError("Mineru API token not found in OCR_API.yaml")
        
        self.client = MineruClient(token)
        self.task_statuses = self._load_task_status()
        self.references = []
        self.logger = logging.getLogger(__name__)
    
    def _load_task_status(self) -> Dict[str, Dict]:
        """Load task status from file"""
        if Path(TASK_STATUS_FILE).exists():
            try:
                with open(TASK_STATUS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_task_status(self):
        """Save task status to file"""
        with open(TASK_STATUS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.task_statuses, f, indent=4, ensure_ascii=False)
    
    def load_references_from_zotero(self):
        """Load references from Zotero"""
        self.logger.info("Loading references from Zotero...")
        
        zotero_config_path = self.config_manager.get_config_path('zotero') if self.config_manager else None
        content, ref_type = fetch_preferred_references(zotero_config_path=str(zotero_config_path))
        
        if not content:
            self.logger.error("Could not fetch references from Zotero")
            return
        
        self._parse_references(content, ref_type)
    
    def load_references_from_bibtex(self, bibtex_path: str):
        """Load references from BibTeX file"""
        self.logger.info(f"Loading references from {bibtex_path}...")
        
        with open(bibtex_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self._parse_references(content, 'biblatex')
    
    def _parse_references(self, content: str, ref_type: str):
        """Parse references from content"""
        if ref_type != 'biblatex':
            self.logger.warning(f"Unsupported reference format: {ref_type}")
            return
        
        parsed_refs = parse_biblatex_content(content)
        self.references = []
        
        for entry in parsed_refs:
            citation_key = entry['ID']
            file_paths = entry.get('file_paths', [])
            
            if file_paths:
                # Local PDF file
                path = file_paths[0]
                self.references.append({
                    'citation_key': citation_key,
                    'type': 'local',
                    'local_pdf_path': path
                })
            elif entry.get('url') and entry['url'].lower().endswith('.pdf'):
                # PDF URL
                self.references.append({
                    'citation_key': citation_key,
                    'type': 'url',
                    'pdf_url': entry['url']
                })
        
        self.logger.info(f"Parsed {len(self.references)} references with PDF")
    
    def process_pending(self):
        """Check and update pending tasks"""
        self.logger.info("Checking pending tasks...")
        
        # Check batch results
        batch_ids = set(
            v['batch_id'] for v in self.task_statuses.values()
            if v.get('batch_id') and v.get('status') not in ['downloaded', 'failed', 'done', 'upload_failed']
        )
        
        for bid in batch_ids:
            results = self.client.get_batch_results(bid)
            if results:
                for res in results:
                    ckey = res.get('data_id')
                    if ckey in self.task_statuses:
                        self.task_statuses[ckey].update(res)
                        self.task_statuses[ckey]['status'] = res.get('state')
        
        # Check single task results
        for key, v in self.task_statuses.items():
            if v.get('task_id') and v.get('status') not in ['downloaded', 'failed', 'done']:
                res = self.client.get_task_result(v['task_id'])
                if res:
                    v.update(res)
                    v['status'] = res.get('state')
        
        self._save_task_status()
    
    def submit_new_tasks(self, max_workers: int = 5):
        """Submit new tasks for processing"""
        self.logger.info("Submitting new tasks...")
        
        # Filter references that need processing
        to_process = [
            ref for ref in self.references
            if ref['citation_key'] not in self.task_statuses
            or self.task_statuses[ref['citation_key']].get('status') == 'pending'
        ]
        
        if not to_process:
            self.logger.info("No new tasks to submit")
            return
        
        # Separate by type
        url_refs = [r for r in to_process if r['type'] == 'url']
        local_refs = [r for r in to_process if r['type'] == 'local']
        
        # Submit URL tasks
        for ref in url_refs:
            task_id = self.client.create_task(ref['pdf_url'])
            if task_id:
                self.task_statuses[ref['citation_key']] = {
                    'task_id': task_id,
                    'status': 'processing',
                    'type': 'url'
                }
        
        # Submit local file batch (simplified - actual implementation would upload files)
        if local_refs:
            self.logger.warning("Local file upload not fully implemented yet")
        
        self._save_task_status()
    
    def download_results(self, max_workers: int = 5) -> int:
        """
        Download completed results
        
        Args:
            max_workers: Maximum concurrent downloads
            
        Returns:
            Number of successfully downloaded files
        """
        self.logger.info("Downloading results...")
        
        # Find tasks ready for download
        to_download = [
            (key, task) for key, task in self.task_statuses.items()
            if task.get('status') == 'done' and task.get('download_url')
        ]
        
        if not to_download:
            self.logger.info("No results ready for download")
            return 0
        
        downloaded_count = 0
        
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._download_single, key, task): key
                for key, task in to_download
            }
            
            for future in as_completed(futures):
                key = futures[future]
                try:
                    if future.result():
                        downloaded_count += 1
                        self.task_statuses[key]['status'] = 'downloaded'
                except Exception as e:
                    self.logger.error(f"Download failed for {key}: {e}")
                    self.task_statuses[key]['status'] = 'failed'
        
        self._save_task_status()
        return downloaded_count
    
    def _download_single(self, key: str, task: Dict) -> bool:
        """Download single result"""
        download_url = task.get('download_url')
        if not download_url:
            return False
        
        # Download ZIP
        zip_content = self.client.download_result(download_url)
        if not zip_content:
            return False
        
        # Extract ZIP
        try:
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # Create output directory for this paper
                paper_dir = self.output_dir / key
                paper_dir.mkdir(parents=True, exist_ok=True)
                
                # Extract all files
                zf.extractall(paper_dir)
                
                self.logger.info(f"Downloaded: {key}")
                return True
        except Exception as e:
            self.logger.error(f"Extract failed for {key}: {e}")
            return False
