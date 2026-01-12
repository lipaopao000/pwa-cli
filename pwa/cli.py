"""
Main CLI application for PWA
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

from .config import ConfigManager
from .session import SessionManager
from .ui import (
    Colors,
    InteractiveMenu,
    MenuOption,
    print_error,
    print_info,
    print_interactive_status,
    print_success,
)
from .version import __description__, __version__


class PWAApplication:
    """Main PWA CLI Application"""

    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize PWA application

        Args:
            config_dir: Custom configuration directory
        """
        self.config_manager = ConfigManager(config_dir)
        self.session_manager = SessionManager()

        # Start or resume session
        self.session = self.session_manager.start_session(resume_last=True)

        self.context = {
            "config_manager": self.config_manager,
            "session_manager": self.session_manager,
            "version": __version__,
        }

        # Initialize commands
        self._init_commands()

    def _init_commands(self):
        """Initialize command instances"""
        from .commands.citations import CitationsReplaceCommand
        from .commands.fulltext import (
            FullTextDownloadCommand,
            FullTextRetryCommand,
            FullTextStatusCommand,
        )
        from .commands.references import ReferencesMatchCommand
        from .commands.session import (
            SessionCleanupCommand,
            SessionExportCommand,
            SessionHistoryCommand,
            SessionListCommand,
            SessionResumeCommand,
            SessionStatsCommand,
            SessionViewCommand,
        )
        from .commands.verify import (
            VerifyExportReportCommand,
            VerifyStatementsCommand,
            VerifyViewResultsCommand,
        )
        from .commands.workflow import (
            WorkflowHistoryCommand,
            WorkflowRunCustomCommand,
            WorkflowRunFullCommand,
        )

        self.commands = {
            "references_match": ReferencesMatchCommand(self.config_manager),
            "citations_replace": CitationsReplaceCommand(self.config_manager),
            "fulltext_download": FullTextDownloadCommand(self.config_manager),
            "fulltext_status": FullTextStatusCommand(self.config_manager),
            "fulltext_retry": FullTextRetryCommand(self.config_manager),
            "verify_statements": VerifyStatementsCommand(self.config_manager),
            "verify_view_results": VerifyViewResultsCommand(self.config_manager),
            "verify_export_report": VerifyExportReportCommand(self.config_manager),
            "workflow_run_full": WorkflowRunFullCommand(self.config_manager),
            "workflow_run_custom": WorkflowRunCustomCommand(self.config_manager),
            "workflow_history": WorkflowHistoryCommand(self.config_manager),
            "session_view": SessionViewCommand(self.config_manager),
            "session_history": SessionHistoryCommand(self.config_manager),
            "session_list": SessionListCommand(self.config_manager),
            "session_resume": SessionResumeCommand(self.config_manager),
            "session_cleanup": SessionCleanupCommand(self.config_manager),
            "session_export": SessionExportCommand(self.config_manager),
            "session_stats": SessionStatsCommand(self.config_manager),
        }

    def run_interactive(self):
        """Run interactive menu mode"""
        self._show_welcome()
        self._create_main_menu().run(self.context)
        self._show_goodbye()

    def _show_welcome(self):
        """Show welcome message"""
        print("\n" + "=" * 60)
        print(Colors.highlight(f"  Paper Writing Assistant (PWA) v{__version__}"))
        print("  " + __description__)
        print("=" * 60)

        # Show session info
        if self.session:
            print(f"\n{Colors.DIM}Session: {self.session.session_id}{Colors.RESET}")
            print(f"{Colors.DIM}工作目录: {self.session.working_directory}{Colors.RESET}")

        print()
        print_interactive_status()
        print()

    def _show_goodbye(self):
        """Show goodbye message"""
        # Save session before exit
        if self.session_manager:
            self.session_manager.save_current_session()

        print("\n" + Colors.info("感谢使用 PWA！再见！") + "\n")

    def _create_main_menu(self) -> InteractiveMenu:
        """Create main menu"""
        options = [
            MenuOption(
                key="1",
                label="参考文献管理",
                description="提取、匹配、导出参考文献",
                submenu=self._create_references_menu(),
            ),
            MenuOption(
                key="2",
                label="引用处理",
                description="替换引用格式",
                submenu=self._create_citations_menu(),
            ),
            MenuOption(
                key="3",
                label="全文获取",
                description="下载论文全文",
                submenu=self._create_fulltext_menu(),
            ),
            MenuOption(
                key="4",
                label="陈述验证",
                description="验证科学陈述",
                submenu=self._create_verify_menu(),
            ),
            MenuOption(
                key="5",
                label="工作流管理",
                description="运行完整工作流",
                submenu=self._create_workflow_menu(),
            ),
            MenuOption(
                key="6",
                label="Session 管理",
                description="查看和管理 Session",
                submenu=self._create_session_menu(),
            ),
            MenuOption(
                key="7",
                label="配置管理",
                description="管理配置文件",
                submenu=self._create_config_menu(),
            ),
            MenuOption(
                key="8",
                label="帮助与文档",
                description="查看帮助文档",
                submenu=self._create_help_menu(),
            ),
        ]

        return InteractiveMenu(
            title=f"Paper Writing Assistant - v{__version__}",
            options=options,
            show_back=False,
            show_quit=True,
        )

    def _create_references_menu(self) -> InteractiveMenu:
        """Create references management menu"""
        options = [
            MenuOption(
                key="1",
                label="匹配参考文献",
                description="从 Markdown 提取并匹配参考文献",
                action=self._run_command("references_match"),
            ),
            MenuOption(
                key="2",
                label="查看匹配结果",
                description="查看参考文献匹配结果",
                action=lambda ctx: print_info("功能开发中..."),
            ),
            MenuOption(
                key="3",
                label="导出参考文献",
                description="导出参考文献到 BibTeX",
                action=lambda ctx: print_info("功能开发中..."),
            ),
            MenuOption(
                key="4",
                label="同步 Zotero 库",
                description="同步 Zotero 参考文献库",
                action=lambda ctx: print_info("功能开发中..."),
            ),
        ]

        return InteractiveMenu(
            title="参考文献管理", options=options, show_back=True, show_quit=False
        )

    def _create_citations_menu(self) -> InteractiveMenu:
        """Create citations menu"""
        options = [
            MenuOption(
                key="1",
                label="替换引用格式",
                description="将上标引用替换为 Pandoc 格式",
                action=self._run_command("citations_replace"),
            ),
            MenuOption(
                key="2",
                label="验证引用",
                description="验证引用格式正确性",
                action=lambda ctx: print_info("功能开发中..."),
            ),
            MenuOption(
                key="3",
                label="生成引用报告",
                description="生成引用统计报告",
                action=lambda ctx: print_info("功能开发中..."),
            ),
        ]

        return InteractiveMenu(title="引用处理", options=options, show_back=True, show_quit=False)

    def _create_fulltext_menu(self) -> InteractiveMenu:
        """Create fulltext menu"""
        options = [
            MenuOption(
                key="1",
                label="下载全文",
                description="使用 Mineru API 下载论文全文",
                action=self._run_command("fulltext_download"),
            ),
            MenuOption(
                key="2",
                label="查看下载状态",
                description="查看全文下载状态",
                action=self._run_command("fulltext_status"),
            ),
            MenuOption(
                key="3",
                label="重试失败任务",
                description="重试失败的下载任务",
                action=self._run_command("fulltext_retry"),
            ),
        ]

        return InteractiveMenu(title="全文获取", options=options, show_back=True, show_quit=False)

    def _create_verify_menu(self) -> InteractiveMenu:
        """Create verify menu"""
        options = [
            MenuOption(
                key="1",
                label="验证科学陈述",
                description="使用 RAGFlow 和 PubMed 验证陈述",
                action=self._run_command("verify_statements"),
            ),
            MenuOption(
                key="2",
                label="查看验证结果",
                description="查看陈述验证结果",
                action=self._run_command("verify_view_results"),
            ),
            MenuOption(
                key="3",
                label="导出验证报告",
                description="导出验证报告",
                action=self._run_command("verify_export_report"),
            ),
        ]

        return InteractiveMenu(title="陈述验证", options=options, show_back=True, show_quit=False)

    def _create_workflow_menu(self) -> InteractiveMenu:
        """Create workflow menu"""
        options = [
            MenuOption(
                key="1",
                label="运行完整工作流",
                description="运行完整的论文处理工作流",
                action=self._run_command("workflow_run_full"),
            ),
            MenuOption(
                key="2",
                label="运行自定义工作流",
                description="选择步骤运行自定义工作流",
                action=self._run_command("workflow_run_custom"),
            ),
            MenuOption(
                key="3",
                label="查看工作流历史",
                description="查看工作流执行历史",
                action=self._run_command("workflow_history"),
            ),
        ]

        return InteractiveMenu(title="工作流管理", options=options, show_back=True, show_quit=False)

    def _create_session_menu(self) -> InteractiveMenu:
        """Create session menu"""
        options = [
            MenuOption(
                key="1",
                label="查看当前 Session",
                description="查看当前 Session 详情",
                action=self._run_command("session_view"),
            ),
            MenuOption(
                key="2",
                label="查看操作历史",
                description="查看 Session 操作历史",
                action=self._run_command("session_history"),
            ),
            MenuOption(
                key="3",
                label="列出所有 Session",
                description="列出所有 Session",
                action=self._run_command("session_list"),
            ),
            MenuOption(
                key="4",
                label="恢复历史 Session",
                description="恢复并切换到历史 Session",
                action=self._run_command("session_resume"),
            ),
            MenuOption(
                key="5",
                label="清理旧 Session",
                description="删除旧的 Session 文件",
                action=self._run_command("session_cleanup"),
            ),
            MenuOption(
                key="6",
                label="导出 Session",
                description="导出 Session 到文件",
                action=self._run_command("session_export"),
            ),
            MenuOption(
                key="7",
                label="Session 统计",
                description="查看 Session 统计信息",
                action=self._run_command("session_stats"),
            ),
        ]

        return InteractiveMenu(
            title="Session 管理", options=options, show_back=True, show_quit=False
        )

    def _create_config_menu(self) -> InteractiveMenu:
        """Create config menu"""
        options = [
            MenuOption(
                key="1",
                label="查看配置",
                description="查看当前配置",
                action=lambda ctx: print_info("功能开发中..."),
            ),
            MenuOption(
                key="2",
                label="编辑配置",
                description="编辑配置文件",
                action=lambda ctx: print_info("功能开发中..."),
            ),
            MenuOption(
                key="3",
                label="重置配置",
                description="重置为默认配置",
                action=lambda ctx: print_info("功能开发中..."),
            ),
        ]

        return InteractiveMenu(title="配置管理", options=options, show_back=True, show_quit=False)

    def _create_help_menu(self) -> InteractiveMenu:
        """Create help menu"""
        options = [
            MenuOption(
                key="1",
                label="用户指南",
                description="查看用户指南",
                action=lambda ctx: print_info("功能开发中..."),
            ),
            MenuOption(
                key="2",
                label="命令参考",
                description="查看命令参考",
                action=lambda ctx: print_info("功能开发中..."),
            ),
            MenuOption(
                key="3",
                label="配置说明",
                description="查看配置说明",
                action=lambda ctx: print_info("功能开发中..."),
            ),
            MenuOption(key="4", label="关于", description="关于 PWA-CLI", action=self._show_about),
        ]

        return InteractiveMenu(title="帮助与文档", options=options, show_back=True, show_quit=False)

    def _run_command(self, command_name: str):
        """Create a function to run a command"""

        def run(context):
            command = self.commands.get(command_name)
            if not command:
                print_error(f"命令未找到: {command_name}")
                return

            # Start command timing
            self.session_manager.start_command()

            try:
                # Get parameters interactively
                params = command.get_interactive_params(context)

                # Validate parameters
                if not command.validate(**params):
                    print_error("参数验证失败")
                    return

                # Execute command
                print_info(f"\n执行命令: {command.description}")
                result = command.execute(**params, **context)

                # Record in session history
                self.session_manager.end_command(command=command_name, params=params, result=result)

                # Update context with result
                if result.get("status") == "success":
                    # Update context based on command type
                    if "md_file" in params:
                        self.session_manager.set_context("last_md_file", params["md_file"])
                    if "bib_file" in params:
                        self.session_manager.set_context("last_bib_file", params["bib_file"])
                    if "output_file" in result:
                        self.session_manager.set_context("last_output_file", result["output_file"])

                input(f"\n{Colors.DIM}按 Enter 继续...{Colors.RESET}")

            except KeyboardInterrupt:
                print(f"\n{Colors.YELLOW}操作已取消{Colors.RESET}")
                self.session_manager.end_command(
                    command=command_name, params={}, result={"status": "cancelled"}
                )
            except Exception as e:
                print_error(f"执行失败: {str(e)}")
                self.session_manager.end_command(
                    command=command_name, params={}, result={"status": "error", "error": str(e)}
                )
                input(f"\n{Colors.DIM}按 Enter 继续...{Colors.RESET}")

        return run

    def _show_about(self, context):
        """Show about information"""
        print("\n" + "=" * 60)
        print(Colors.highlight("关于 PWA-CLI"))
        print("=" * 60 + "\n")

        print(f"版本: {__version__}")
        print(f"描述: {__description__}")
        print(f"GitHub: https://github.com/lipaopao000/pwa-cli")
        print(f"\n作者: lipaopao000")
        print(f"许可: MIT License")

        print("\n" + "=" * 60 + "\n")

        input(f"{Colors.DIM}按 Enter 继续...{Colors.RESET}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description=__description__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument("--version", action="version", version=f"PWA-CLI v{__version__}")

    parser.add_argument("--config-dir", type=Path, help="Custom configuration directory")

    args = parser.parse_args()

    try:
        app = PWAApplication(config_dir=args.config_dir)
        app.run_interactive()
    except KeyboardInterrupt:
        print("\n\n" + Colors.warning("程序已中断") + "\n")
        sys.exit(0)
    except Exception as e:
        print_error(f"发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
