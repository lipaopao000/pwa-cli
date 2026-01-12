"""
Full-text retrieval command for PWA CLI
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ..ui import Colors, print_error, print_info, print_success, print_warning
from .base import BaseCommand


class FullTextDownloadCommand(BaseCommand):
    """Download full-text Markdown for papers using Mineru API"""

    name = "fulltext_download"
    description = "下载论文全文 Markdown"

    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.task_status_file = "fulltext_tasks.json"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        print_info("\n=== 全文获取配置 ===\n")

        # Get reference source
        print("参考文献来源:")
        print("  1. Zotero API")
        print("  2. 本地 BibTeX 文件")

        source_choice = self.prompt_choice("请选择", ["1", "2"])

        if source_choice == "1":
            ref_source = "zotero"
            ref_path = None
        else:
            ref_path = self.prompt_file("请输入 BibTeX 文件路径")
            ref_source = "bibtex"

        # Get output directory
        default_output = "./FullTextMD"
        output_dir = self.prompt_text(f"输出目录 (默认: {default_output})", default=default_output)

        # Get concurrency
        max_workers = self.prompt_text("并发下载数 (默认: 5)", default="5")

        try:
            max_workers = int(max_workers)
        except ValueError:
            max_workers = 5

        return {
            "ref_source": ref_source,
            "ref_path": ref_path,
            "output_dir": output_dir,
            "max_workers": max_workers,
        }

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        ref_source = kwargs.get("ref_source")
        ref_path = kwargs.get("ref_path")

        if ref_source == "bibtex":
            if not ref_path or not Path(ref_path).exists():
                print_error(f"BibTeX 文件不存在: {ref_path}")
                return False

        # Check OCR API config
        ocr_config = self.config_manager.load_config("ocr")
        if not ocr_config or "mineru_api_token" not in ocr_config:
            print_error("未找到 Mineru API Token")
            print_info("请配置 OCR_API.yaml 文件")
            return False

        return True

    def execute(
        self,
        ref_source: str,
        ref_path: Optional[str] = None,
        output_dir: str = "./FullTextMD",
        max_workers: int = 5,
        **kwargs,
    ) -> Dict:
        """
        Execute full-text download

        Args:
            ref_source: Reference source ('zotero' or 'bibtex')
            ref_path: Path to BibTeX file (if ref_source is 'bibtex')
            output_dir: Output directory for downloaded files
            max_workers: Maximum concurrent downloads

        Returns:
            Dictionary with execution results
        """
        try:
            # Import Mineru client
            from ..clients.mineru import FullTextProcessor, MineruClient

            print_info("\n=== 开始全文获取 ===\n")

            # Initialize processor
            processor = FullTextProcessor(output_dir=output_dir, config_manager=self.config_manager)

            # Load references
            print_info("正在加载参考文献...")
            if ref_source == "zotero":
                processor.load_references_from_zotero()
            else:
                processor.load_references_from_bibtex(ref_path)

            ref_count = len(processor.references)
            print_success(f"已加载 {ref_count} 条参考文献")

            if ref_count == 0:
                print_warning("没有找到可下载的参考文献")
                return {"status": "no_references", "count": 0}

            # Process pending tasks
            print_info("\n正在检查待处理任务...")
            processor.process_pending()

            # Submit new tasks
            print_info("\n正在提交新任务...")
            processor.submit_new_tasks(max_workers=max_workers)

            # Download results
            print_info("\n正在下载结果...")
            downloaded = processor.download_results(max_workers=max_workers)

            # Show summary
            self._show_summary(processor.task_statuses)

            return {
                "status": "success",
                "total": ref_count,
                "downloaded": downloaded,
                "output_dir": output_dir,
            }

        except Exception as e:
            self.logger.error(f"Full-text download failed: {e}", exc_info=True)
            print_error(f"下载失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _show_summary(self, task_statuses: Dict):
        """Show download summary"""
        print_info("\n" + "=" * 60)
        print_info("下载统计")
        print_info("=" * 60 + "\n")

        status_counts = {}
        for task in task_statuses.values():
            status = task.get("status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1

        status_names = {
            "downloaded": "✓ 已下载",
            "done": "✓ 已完成",
            "processing": "⏳ 处理中",
            "pending": "⏳ 等待中",
            "failed": "✗ 失败",
            "upload_failed": "✗ 上传失败",
        }

        for status, count in status_counts.items():
            status_name = status_names.get(status, status)
            print(f"  {status_name}: {count}")

        print()


class FullTextStatusCommand(BaseCommand):
    """View full-text download status"""

    name = "fulltext_status"
    description = "查看全文下载状态"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        return {}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        return True

    def execute(self, **kwargs) -> Dict:
        """Execute status check"""
        task_status_file = "fulltext_tasks.json"

        if not Path(task_status_file).exists():
            print_info("没有找到任务状态文件")
            return {"status": "no_tasks"}

        try:
            with open(task_status_file, "r", encoding="utf-8") as f:
                task_statuses = json.load(f)

            if not task_statuses:
                print_info("没有任务记录")
                return {"status": "empty"}

            self._show_status(task_statuses)

            return {"status": "success", "count": len(task_statuses)}

        except Exception as e:
            self.logger.error(f"Failed to read status: {e}", exc_info=True)
            print_error(f"读取状态失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _show_status(self, task_statuses: Dict):
        """Show task status"""
        print_info("\n" + "=" * 60)
        print_info("任务状态")
        print_info("=" * 60 + "\n")

        # Group by status
        by_status = {}
        for key, task in task_statuses.items():
            status = task.get("status", "unknown")
            if status not in by_status:
                by_status[status] = []
            by_status[status].append((key, task))

        # Show each group
        status_order = ["downloaded", "done", "processing", "pending", "failed", "upload_failed"]
        status_icons = {
            "downloaded": "✓",
            "done": "✓",
            "processing": "⏳",
            "pending": "⏳",
            "failed": "✗",
            "upload_failed": "✗",
        }

        for status in status_order:
            if status not in by_status:
                continue

            tasks = by_status[status]
            icon = status_icons.get(status, "•")
            print(f"{icon} {Colors.highlight(status.upper())} ({len(tasks)} 个)")

            for key, task in tasks[:5]:  # Show first 5
                print(f"  - {key}")

            if len(tasks) > 5:
                print(f"  ... 还有 {len(tasks) - 5} 个")

            print()


class FullTextRetryCommand(BaseCommand):
    """Retry failed full-text downloads"""

    name = "fulltext_retry"
    description = "重试失败的下载任务"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        print_info("\n=== 重试失败任务 ===\n")

        max_workers = self.prompt_text("并发下载数 (默认: 5)", default="5")

        try:
            max_workers = int(max_workers)
        except ValueError:
            max_workers = 5

        return {"max_workers": max_workers}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        return True

    def execute(self, max_workers: int = 5, **kwargs) -> Dict:
        """Execute retry"""
        task_status_file = "fulltext_tasks.json"

        if not Path(task_status_file).exists():
            print_info("没有找到任务状态文件")
            return {"status": "no_tasks"}

        try:
            from ..clients.mineru import FullTextProcessor

            print_info("\n=== 重试失败任务 ===\n")

            # Initialize processor
            processor = FullTextProcessor(
                output_dir="./FullTextMD", config_manager=self.config_manager
            )

            # Count failed tasks
            failed_count = sum(
                1
                for task in processor.task_statuses.values()
                if task.get("status") in ["failed", "upload_failed"]
            )

            if failed_count == 0:
                print_info("没有失败的任务")
                return {"status": "no_failed"}

            print_info(f"找到 {failed_count} 个失败任务")

            # Reset failed tasks
            for key, task in processor.task_statuses.items():
                if task.get("status") in ["failed", "upload_failed"]:
                    task["status"] = "pending"
                    task.pop("task_id", None)
                    task.pop("batch_id", None)

            processor._save_task_status()

            # Retry
            print_info("\n正在重新提交任务...")
            processor.submit_new_tasks(max_workers=max_workers)

            print_info("\n正在下载结果...")
            downloaded = processor.download_results(max_workers=max_workers)

            print_success(f"\n重试完成，成功下载 {downloaded} 个")

            return {"status": "success", "retried": failed_count, "downloaded": downloaded}

        except Exception as e:
            self.logger.error(f"Retry failed: {e}", exc_info=True)
            print_error(f"重试失败: {str(e)}")
            return {"status": "error", "error": str(e)}
