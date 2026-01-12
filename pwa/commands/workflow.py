"""
Workflow management command for PWA CLI
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from ..ui import Colors, print_error, print_info, print_success, print_warning
from .base import BaseCommand


class WorkflowRunFullCommand(BaseCommand):
    """Run complete workflow"""

    name = "workflow_run_full"
    description = "运行完整工作流"

    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.workflow_history_file = "workflow_history.json"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        print_info("\n=== 完整工作流配置 ===\n")
        print_info("完整工作流包括以下步骤:")
        print("  1. 参考文献匹配")
        print("  2. 引用替换")
        print("  3. 全文获取")
        print("  4. 陈述验证")
        print()

        # Get input file
        md_file = self.prompt_file("请输入 Markdown 文件路径")

        # Get reference source
        print("\n参考文献来源:")
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
        default_output = "./workflow_output"
        output_dir = self.prompt_text(f"输出目录 (默认: {default_output})", default=default_output)

        return {
            "md_file": md_file,
            "ref_source": ref_source,
            "ref_path": ref_path,
            "output_dir": output_dir,
        }

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        md_file = kwargs.get("md_file")

        if not md_file or not Path(md_file).exists():
            print_error(f"Markdown 文件不存在: {md_file}")
            return False

        ref_source = kwargs.get("ref_source")
        ref_path = kwargs.get("ref_path")

        if ref_source == "bibtex":
            if not ref_path or not Path(ref_path).exists():
                print_error(f"BibTeX 文件不存在: {ref_path}")
                return False

        return True

    def execute(
        self,
        md_file: str,
        ref_source: str,
        ref_path: Optional[str] = None,
        output_dir: str = "./workflow_output",
        **kwargs,
    ) -> Dict:
        """
        Execute complete workflow

        Args:
            md_file: Path to Markdown file
            ref_source: Reference source ('zotero' or 'bibtex')
            ref_path: Path to BibTeX file (if ref_source is 'bibtex')
            output_dir: Output directory

        Returns:
            Dictionary with execution results
        """
        try:
            from .citations import CitationsReplaceCommand
            from .fulltext import FullTextDownloadCommand
            from .references import ReferencesMatchCommand
            from .verify import VerifyStatementsCommand

            print_info("\n" + "=" * 60)
            print_info("开始运行完整工作流")
            print_info("=" * 60 + "\n")

            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)

            workflow_results = {
                "start_time": datetime.now().isoformat(),
                "md_file": md_file,
                "ref_source": ref_source,
                "output_dir": output_dir,
                "steps": [],
            }

            # Step 1: References Match
            print_info("步骤 1/4: 参考文献匹配")
            print_info("-" * 60 + "\n")

            ref_cmd = ReferencesMatchCommand(self.config_manager)
            ref_result = ref_cmd.execute(
                md_file=md_file, ref_source=ref_source, ref_path=ref_path, fuzzy_candidates=3
            )

            workflow_results["steps"].append(
                {
                    "step": 1,
                    "name": "references_match",
                    "status": ref_result.get("status"),
                    "result": ref_result,
                }
            )

            if ref_result.get("status") != "success":
                print_error("参考文献匹配失败，工作流终止")
                return self._save_workflow_result(workflow_results, "failed")

            print_success("✓ 参考文献匹配完成\n")

            # Step 2: Citations Replace
            print_info("步骤 2/4: 引用替换")
            print_info("-" * 60 + "\n")

            replaced_file = str(output_path / "paper_replaced.md")

            cit_cmd = CitationsReplaceCommand(self.config_manager)
            cit_result = cit_cmd.execute(
                md_file=md_file,
                match_file="./config-and-cache/references_match.json",
                output_file=replaced_file,
            )

            workflow_results["steps"].append(
                {
                    "step": 2,
                    "name": "citations_replace",
                    "status": cit_result.get("status"),
                    "result": cit_result,
                }
            )

            if cit_result.get("status") != "success":
                print_error("引用替换失败，工作流终止")
                return self._save_workflow_result(workflow_results, "failed")

            print_success("✓ 引用替换完成\n")

            # Step 3: Full-text Download
            print_info("步骤 3/4: 全文获取")
            print_info("-" * 60 + "\n")

            fulltext_dir = str(output_path / "FullTextMD")

            full_cmd = FullTextDownloadCommand(self.config_manager)
            full_result = full_cmd.execute(
                ref_source=ref_source, ref_path=ref_path, output_dir=fulltext_dir, max_workers=5
            )

            workflow_results["steps"].append(
                {
                    "step": 3,
                    "name": "fulltext_download",
                    "status": full_result.get("status"),
                    "result": full_result,
                }
            )

            if full_result.get("status") not in ["success", "no_references"]:
                print_warning("全文获取失败，继续下一步")
            else:
                print_success("✓ 全文获取完成\n")

            # Step 4: Statement Verification
            print_info("步骤 4/4: 陈述验证")
            print_info("-" * 60 + "\n")

            verify_output = str(output_path / "verification_results.json")

            verify_cmd = VerifyStatementsCommand(self.config_manager)
            verify_result = verify_cmd.execute(
                md_file=replaced_file,
                use_ragflow=True,
                use_pubmed=True,
                max_workers=3,
                output_file=verify_output,
            )

            workflow_results["steps"].append(
                {
                    "step": 4,
                    "name": "verify_statements",
                    "status": verify_result.get("status"),
                    "result": verify_result,
                }
            )

            if verify_result.get("status") != "success":
                print_warning("陈述验证失败")
            else:
                print_success("✓ 陈述验证完成\n")

            # Complete
            workflow_results["end_time"] = datetime.now().isoformat()
            workflow_results["status"] = "success"

            print_info("\n" + "=" * 60)
            print_success("完整工作流执行完成！")
            print_info("=" * 60 + "\n")

            self._show_summary(workflow_results)

            return self._save_workflow_result(workflow_results, "success")

        except Exception as e:
            self.logger.error(f"Workflow failed: {e}", exc_info=True)
            print_error(f"工作流失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _save_workflow_result(self, workflow_results: Dict, status: str) -> Dict:
        """Save workflow result to history"""
        workflow_results["status"] = status

        # Load history
        history = []
        if Path(self.workflow_history_file).exists():
            try:
                with open(self.workflow_history_file, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                pass

        # Add current workflow
        history.append(workflow_results)

        # Save history
        with open(self.workflow_history_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)

        return workflow_results

    def _show_summary(self, workflow_results: Dict):
        """Show workflow summary"""
        print_info("工作流摘要:\n")

        for step in workflow_results["steps"]:
            step_num = step["step"]
            step_name = step["name"]
            step_status = step["status"]

            if step_status == "success":
                icon = "✓"
                color = Colors.success
            elif step_status in ["failed", "error"]:
                icon = "✗"
                color = Colors.error
            else:
                icon = "⚠"
                color = Colors.warning

            print(f"  {icon} 步骤 {step_num}: {step_name} - {color(step_status)}")

        print()
        print(f"输出目录: {Colors.highlight(workflow_results['output_dir'])}")
        print()


class WorkflowRunCustomCommand(BaseCommand):
    """Run custom workflow"""

    name = "workflow_run_custom"
    description = "运行自定义工作流"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        print_info("\n=== 自定义工作流配置 ===\n")
        print_info("可用步骤:")
        print("  1. 参考文献匹配")
        print("  2. 引用替换")
        print("  3. 全文获取")
        print("  4. 陈述验证")
        print()

        steps_input = self.prompt_text("请选择要执行的步骤 (例如: 1,2,4)", default="1,2")

        # Parse steps
        try:
            steps = [int(s.strip()) for s in steps_input.split(",")]
        except ValueError:
            steps = [1, 2]

        # Get input file
        md_file = self.prompt_file("请输入 Markdown 文件路径")

        return {"md_file": md_file, "steps": steps}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        md_file = kwargs.get("md_file")

        if not md_file or not Path(md_file).exists():
            print_error(f"Markdown 文件不存在: {md_file}")
            return False

        return True

    def execute(self, md_file: str, steps: List[int], **kwargs) -> Dict:
        """Execute custom workflow"""
        print_info("\n自定义工作流功能开发中...")
        print_info(f"将执行步骤: {steps}")

        return {"status": "not_implemented", "steps": steps}


class WorkflowHistoryCommand(BaseCommand):
    """View workflow history"""

    name = "workflow_history"
    description = "查看工作流历史"

    def __init__(self, config_manager):
        super().__init__(config_manager)
        self.workflow_history_file = "workflow_history.json"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        return {}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        return True

    def execute(self, **kwargs) -> Dict:
        """Execute view history"""
        if not Path(self.workflow_history_file).exists():
            print_info("没有工作流历史记录")
            return {"status": "no_history"}

        try:
            with open(self.workflow_history_file, "r", encoding="utf-8") as f:
                history = json.load(f)

            if not history:
                print_info("工作流历史为空")
                return {"status": "empty"}

            self._show_history(history)

            return {"status": "success", "count": len(history)}

        except Exception as e:
            self.logger.error(f"Failed to read history: {e}", exc_info=True)
            print_error(f"读取历史失败: {str(e)}")
            return {"status": "error", "error": str(e)}

    def _show_history(self, history: List[Dict]):
        """Show workflow history"""
        print_info("\n" + "=" * 60)
        print_info("工作流历史")
        print_info("=" * 60 + "\n")

        for i, workflow in enumerate(reversed(history[-10:]), 1):  # Show last 10
            start_time = workflow.get("start_time", "unknown")
            status = workflow.get("status", "unknown")
            md_file = workflow.get("md_file", "unknown")

            if status == "success":
                icon = "✓"
            elif status == "failed":
                icon = "✗"
            else:
                icon = "⚠"

            print(f"{i}. {icon} {start_time}")
            print(f"   文件: {md_file}")
            print(f"   状态: {status}")

            steps = workflow.get("steps", [])
            if steps:
                print(f"   步骤: {len(steps)} 个")

            print()
