"""
Full-text processor for PDF to Markdown conversion
Handles the business logic of managing tasks, references, and files.
"""

import io
import json
import logging
import zipfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..clients.mineru import MineruClient, TaskOptions
from ..clients.zotero import fetch_preferred_references
from .utils import parse_biblatex_content

# Constants
TASK_STATUS_FILE = "fulltext_tasks.json"


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
        ocr_config = config_manager.load_config("ocr") if config_manager else {}
        token = ocr_config.get("mineru_api_token")

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
                with open(TASK_STATUS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_task_status(self):
        """Save task status to file"""
        with open(TASK_STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.task_statuses, f, indent=4, ensure_ascii=False)

    def load_references_from_zotero(self):
        """Load references from Zotero"""
        self.logger.info("Loading references from Zotero...")

        zotero_config_path = (
            self.config_manager.get_config_path("zotero") if self.config_manager else None
        )
        content, ref_type = fetch_preferred_references(zotero_config_path=str(zotero_config_path))

        if not content:
            self.logger.error("Could not fetch references from Zotero")
            return

        self._parse_references(content, ref_type)

    def load_references_from_bibtex(self, bibtex_path: str):
        """Load references from BibTeX file"""
        self.logger.info(f"Loading references from {bibtex_path}...")

        with open(bibtex_path, "r", encoding="utf-8") as f:
            content = f.read()

        self._parse_references(content, "biblatex")

    def _parse_references(self, content: str, ref_type: str):
        """Parse references from content"""
        if ref_type != "biblatex":
            self.logger.warning(f"Unsupported reference format: {ref_type}")
            return

        parsed_refs = parse_biblatex_content(content)
        self.references = []

        for entry in parsed_refs:
            citation_key = entry["ID"]
            file_paths = entry.get("file_paths", [])

            if file_paths:
                # Local PDF file
                path = file_paths[0]
                self.references.append(
                    {"citation_key": citation_key, "type": "local", "local_pdf_path": path}
                )
            elif entry.get("url") and entry["url"].lower().endswith(".pdf"):
                # PDF URL
                self.references.append(
                    {"citation_key": citation_key, "type": "url", "pdf_url": entry["url"]}
                )

        self.logger.info(f"Parsed {len(self.references)} references with PDF")

    def process_pending(self):
        """Check and update pending tasks"""
        self.logger.info("Checking pending tasks...")

        # Check batch results
        batch_ids = set(
            v["batch_id"]
            for v in self.task_statuses.values()
            if v.get("batch_id")
            and v.get("status") not in ["downloaded", "failed", "done", "upload_failed"]
        )

        for bid in batch_ids:
            try:
                results = self.client.get_batch_results(bid)
                if results:
                    for res in results:
                        ckey = res.get("data_id")
                        if ckey in self.task_statuses:
                            self.task_statuses[ckey].update(res)
                            self.task_statuses[ckey]["status"] = res.get("state")
            except Exception as e:
                self.logger.error(f"Failed to get batch results for {bid}: {e}")

        # Check single task results
        for key, v in self.task_statuses.items():
            if v.get("task_id") and v.get("status") not in ["downloaded", "failed", "done"]:
                try:
                    res = self.client.get_task_result(v["task_id"])
                    if res:
                        v.update(res)
                        v["status"] = res.get("state")
                except Exception as e:
                    self.logger.error(f"Failed to get task result for {key}: {e}")

        self._save_task_status()

    def submit_new_tasks(self, max_workers: int = 5):
        """Submit new tasks for processing"""
        self.logger.info("Submitting new tasks...")

        # Filter references that need processing
        to_process = [
            ref
            for ref in self.references
            if ref["citation_key"] not in self.task_statuses
            or self.task_statuses[ref["citation_key"]].get("status") in ["pending", None]
        ]

        if not to_process:
            self.logger.info("No new tasks to submit")
            return

        # Separate by type
        url_refs = [r for r in to_process if r["type"] == "url"]
        local_refs = [r for r in to_process if r["type"] == "local"]

        # Submit URL tasks
        for ref in url_refs:
            try:
                task_id = self.client.create_task(ref["pdf_url"])
                if task_id:
                    self.task_statuses[ref["citation_key"]] = {
                        "task_id": task_id,
                        "status": "processing",
                        "type": "url",
                    }
            except Exception as e:
                self.logger.error(f"Failed to submit task for {ref['citation_key']}: {e}")
                self.task_statuses[ref["citation_key"]] = {
                    "status": "failed",
                    "err_msg": str(e),
                    "type": "url",
                }

        # Submit local file batch (placeholder for future implementation)
        if local_refs:
            self.logger.warning("Local file upload not fully implemented yet in FullTextProcessor")

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
            (key, task)
            for key, task in self.task_statuses.items()
            if task.get("status") == "done" and task.get("full_zip_url")
        ]

        if not to_download:
            self.logger.info("No results ready for download")
            return 0

        downloaded_count = 0

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._download_single, key, task): key for key, task in to_download
            }

            for future in as_completed(futures):
                key = futures[future]
                try:
                    if future.result():
                        downloaded_count += 1
                        self.task_statuses[key]["status"] = "downloaded"
                    else:
                        self.task_statuses[key]["status"] = "failed"
                except Exception as e:
                    self.logger.error(f"Download failed for {key}: {e}")
                    self.task_statuses[key]["status"] = "failed"

        self._save_task_status()
        return downloaded_count

    def _download_single(self, key: str, task: Dict) -> bool:
        """Download single result"""
        download_url = task.get("full_zip_url")
        if not download_url:
            return False

        # Download ZIP
        try:
            zip_content = self.client.download_result(download_url)
            if not zip_content:
                return False

            # Extract ZIP
            with zipfile.ZipFile(io.BytesIO(zip_content)) as zf:
                # Create output directory for this paper
                paper_dir = self.output_dir / key
                paper_dir.mkdir(parents=True, exist_ok=True)

                # Extract all files
                zf.extractall(paper_dir)

                self.logger.info(f"Downloaded and extracted: {key}")
                return True
        except Exception as e:
            self.logger.error(f"Download/Extract failed for {key}: {e}")
            return False
