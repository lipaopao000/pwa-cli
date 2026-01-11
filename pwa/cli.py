"""
Main CLI application for PWA
"""

import sys
import argparse
from pathlib import Path
from typing import Optional

from .version import __version__, __description__
from .config import ConfigManager
from .ui import MenuBuilder, print_success, print_error, print_info, Colors


class PWAApplication:
    """Main PWA CLI Application"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        """
        Initialize PWA application
        
        Args:
            config_dir: Custom configuration directory
        """
        self.config_manager = ConfigManager(config_dir)
        self.context = {
            'config_manager': self.config_manager,
            'version': __version__
        }
        
        # Initialize commands
        self._init_commands()
    
    def _init_commands(self):
        """Initialize command instances"""
        from .commands.references import ReferencesMatchCommand
        from .commands.citations import CitationsReplaceCommand
        from .commands.fulltext import FullTextDownloadCommand, FullTextStatusCommand, FullTextRetryCommand
        from .commands.verify import VerifyStatementsCommand, VerifyViewResultsCommand, VerifyExportReportCommand
        from .commands.workflow import WorkflowRunFullCommand, WorkflowRunCustomCommand, WorkflowHistoryCommand
        
        self.commands = {
            'references_match': ReferencesMatchCommand(self.config_manager),
            'citations_replace': CitationsReplaceCommand(self.config_manager),
            'fulltext_download': FullTextDownloadCommand(self.config_manager),
            'fulltext_status': FullTextStatusCommand(self.config_manager),
            'fulltext_retry': FullTextRetryCommand(self.config_manager),
            'verify_statements': VerifyStatementsCommand(self.config_manager),
            'verify_view_results': VerifyViewResultsCommand(self.config_manager),
            'verify_export_report': VerifyExportReportCommand(self.config_manager),
            'workflow_run_full': WorkflowRunFullCommand(self.config_manager),
            'workflow_run_custom': WorkflowRunCustomCommand(self.config_manager),
            'workflow_history': WorkflowHistoryCommand(self.config_manager),
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
        print("=" * 60 + "\n")
    
    def _show_goodbye(self):
        """Show goodbye message"""
        print("\n" + Colors.info("感谢使用 PWA！再见！") + "\n")
    
    def _create_main_menu(self):
        """Create main menu"""
        builder = MenuBuilder(f"Paper Writing Assistant - v{__version__}")
        
        builder.add_item("1", "参考文献管理", self._references_menu)
        builder.add_item("2", "引用处理", self._citations_menu)
        builder.add_item("3", "全文获取", self._fulltext_menu)
        builder.add_item("4", "陈述验证", self._verify_menu)
        builder.add_separator()
        builder.add_item("5", "工作流管理", self._workflow_menu)
        builder.add_item("6", "配置管理", self._config_menu)
        builder.add_separator()
        builder.add_item("7", "帮助与文档", self._help_menu)
        builder.add_exit()
        
        return builder.build()
    
    def _references_menu(self, context):
        """References management submenu"""
        from .ui import MenuBuilder
        
        menu = MenuBuilder("参考文献管理")
        menu.add_item("1", "匹配参考文献", self._references_match)
        menu.add_item("2", "查看匹配结果", self._references_view_results)
        menu.add_item("3", "导出参考文献", self._references_export)
        menu.add_item("4", "同步 Zotero 库", self._references_sync_zotero)
        menu.add_back()
        
        menu.build().run(context)
    
    def _citations_menu(self, context):
        """Citations processing submenu"""
        from .ui import MenuBuilder
        
        menu = MenuBuilder("引用处理")
        menu.add_item("1", "替换引用格式", self._citations_replace)
        menu.add_item("2", "验证引用完整性", self._citations_validate)
        menu.add_item("3", "生成引用报告", self._citations_report)
        menu.add_back()
        
        menu.build().run(context)
    
    def _fulltext_menu(self, context):
        """Full-text retrieval submenu"""
        from .ui import MenuBuilder
        
        menu = MenuBuilder("全文获取")
        menu.add_item("1", "下载全文 Markdown", self._fulltext_download)
        menu.add_item("2", "查看下载状态", self._fulltext_status)
        menu.add_item("3", "重试失败任务", self._fulltext_retry)
        menu.add_back()
        
        menu.build().run(context)
    
    def _verify_menu(self, context):
        """Statement verification submenu"""
        from .ui import MenuBuilder
        
        menu = MenuBuilder("陈述验证")
        menu.add_item("1", "验证科学陈述", self._verify_statements)
        menu.add_item("2", "查看验证结果", self._verify_view_results)
        menu.add_item("3", "导出验证报告", self._verify_export_report)
        menu.add_back()
        
        menu.build().run(context)
    
    def _workflow_menu(self, context):
        """Workflow management submenu"""
        from .ui import MenuBuilder
        
        menu = MenuBuilder("工作流管理")
        menu.add_item("1", "运行完整工作流", self._workflow_run_full)
        menu.add_item("2", "运行自定义工作流", self._workflow_run_custom)
        menu.add_item("3", "查看工作流历史", self._workflow_history)
        menu.add_back()
        
        menu.build().run(context)
    
    def _config_menu(self, context):
        """Configuration management submenu"""
        from .ui import MenuBuilder
        
        menu = MenuBuilder("配置管理")
        menu.add_item("1", "查看配置列表", self._config_list)
        menu.add_item("2", "编辑 LLM 配置", self._config_edit_llm)
        menu.add_item("3", "编辑 Zotero 配置", self._config_edit_zotero)
        menu.add_item("4", "编辑 RAGFlow 配置", self._config_edit_ragflow)
        menu.add_item("5", "编辑 OCR API 配置", self._config_edit_ocr)
        menu.add_separator()
        menu.add_item("6", "重置配置", self._config_reset)
        menu.add_back()
        
        menu.build().run(context)
    
    def _help_menu(self, context):
        """Help and documentation submenu"""
        from .ui import MenuBuilder
        
        menu = MenuBuilder("帮助与文档")
        menu.add_item("1", "查看用户指南", self._help_user_guide)
        menu.add_item("2", "查看命令参考", self._help_command_reference)
        menu.add_item("3", "查看配置说明", self._help_config_guide)
        menu.add_item("4", "关于 PWA", self._help_about)
        menu.add_back()
        
        menu.build().run(context)
    
    # ========== References Commands ==========
    
    def _references_match(self, context):
        """Match references command"""
        cmd = self.commands['references_match']
        cmd.interactive_execute(context)
    
    def _references_view_results(self, context):
        """View reference matching results"""
        print_info("功能开发中：查看匹配结果")
    
    def _references_export(self, context):
        """Export references"""
        print_info("功能开发中：导出参考文献")
    
    def _references_sync_zotero(self, context):
        """Sync Zotero library"""
        print_info("功能开发中：同步 Zotero 库")
    
    # ========== Citations Commands ==========
    
    def _citations_replace(self, context):
        """Replace citation format"""
        cmd = self.commands['citations_replace']
        cmd.interactive_execute(context)
    
    def _citations_validate(self, context):
        """Validate citations"""
        print_info("功能开发中：验证引用完整性")
    
    def _citations_report(self, context):
        """Generate citation report"""
        print_info("功能开发中：生成引用报告")
    
    # ========== Fulltext Commands ==========
    
    def _fulltext_download(self, context):
        """Download full-text Markdown"""
        cmd = self.commands['fulltext_download']
        cmd.interactive_execute(context)
    
    def _fulltext_status(self, context):
        """View download status"""
        cmd = self.commands['fulltext_status']
        cmd.interactive_execute(context)
    
    def _fulltext_retry(self, context):
        """Retry failed downloads"""
        cmd = self.commands['fulltext_retry']
        cmd.interactive_execute(context)
    
    # ========== Verify Commands ==========
    
    def _verify_statements(self, context):
        """Verify scientific statements"""
        cmd = self.commands['verify_statements']
        cmd.interactive_execute(context)
    
    def _verify_view_results(self, context):
        """View verification results"""
        cmd = self.commands['verify_view_results']
        cmd.interactive_execute(context)
    
    def _verify_export_report(self, context):
        """Export verification report"""
        cmd = self.commands['verify_export_report']
        cmd.interactive_execute(context)
    
    # ========== Workflow Commands ==========
    
    def _workflow_run_full(self, context):
        """Run full workflow"""
        cmd = self.commands['workflow_run_full']
        cmd.interactive_execute(context)
    
    def _workflow_run_custom(self, context):
        """Run custom workflow"""
        cmd = self.commands['workflow_run_custom']
        cmd.interactive_execute(context)
    
    def _workflow_history(self, context):
        """View workflow history"""
        cmd = self.commands['workflow_history']
        cmd.interactive_execute(context)
    
    # ========== Config Commands ==========
    
    def _config_list(self, context):
        """List all configurations"""
        print_info("\n当前配置文件列表：\n")
        configs = self.config_manager.list_configs()
        
        if not configs:
            print_info("未找到配置文件")
            return
        
        for name, path in configs.items():
            print(f"  • {Colors.highlight(name)}: {path}")
        
        print(f"\n配置目录: {Colors.highlight(str(self.config_manager.config_dir))}")
    
    def _config_edit_llm(self, context):
        """Edit LLM configuration"""
        print_info("功能开发中：编辑 LLM 配置")
    
    def _config_edit_zotero(self, context):
        """Edit Zotero configuration"""
        print_info("功能开发中：编辑 Zotero 配置")
    
    def _config_edit_ragflow(self, context):
        """Edit RAGFlow configuration"""
        print_info("功能开发中：编辑 RAGFlow 配置")
    
    def _config_edit_ocr(self, context):
        """Edit OCR API configuration"""
        print_info("功能开发中：编辑 OCR API 配置")
    
    def _config_reset(self, context):
        """Reset configuration"""
        print_info("功能开发中：重置配置")
    
    # ========== Help Commands ==========
    
    def _help_user_guide(self, context):
        """Show user guide"""
        print_info("\n=== PWA 用户指南 ===\n")
        print("PWA (Paper Writing Assistant) 是一个学术写作辅助工具。")
        print("\n主要功能：")
        print("  1. 参考文献管理 - 从 Markdown 提取参考文献并与 Zotero/BibTeX 库匹配")
        print("  2. 引用处理 - 将上标引用替换为 Pandoc BibTeX 格式")
        print("  3. 全文获取 - 使用 Mineru API 获取论文全文 Markdown")
        print("  4. 陈述验证 - 使用 RAGFlow 和 PubMed 验证科学陈述")
        print("\n详细文档请访问: https://github.com/lipaopao000/pwa-cli")
    
    def _help_command_reference(self, context):
        """Show command reference"""
        print_info("功能开发中：命令参考")
    
    def _help_config_guide(self, context):
        """Show configuration guide"""
        print_info("功能开发中：配置说明")
    
    def _help_about(self, context):
        """Show about information"""
        print_info(f"\n=== 关于 PWA ===\n")
        print(f"版本: {__version__}")
        print(f"描述: {__description__}")
        print(f"作者: lipaopao000")
        print(f"仓库: https://github.com/lipaopao000/pwa-cli")
        print(f"许可: MIT License")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description=__description__,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version=f'PWA v{__version__}'
    )
    
    parser.add_argument(
        '--config-dir',
        type=Path,
        help='自定义配置目录'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        default=True,
        help='交互式菜单模式（默认）'
    )
    
    args = parser.parse_args()
    
    try:
        app = PWAApplication(config_dir=args.config_dir)
        
        if args.interactive or len(sys.argv) == 1:
            # Run interactive mode
            app.run_interactive()
        else:
            # Command-line mode (to be implemented)
            print_error("命令行模式尚未实现，请使用交互式模式")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        sys.exit(0)
    except Exception as e:
        print_error(f"发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
