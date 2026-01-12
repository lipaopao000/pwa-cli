"""
Session management commands for PWA CLI
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict

from ..ui import Colors, print_error, print_info, print_success, print_warning
from .base import BaseCommand


class SessionViewCommand(BaseCommand):
    """View current session details"""

    name = "session_view"
    description = "查看当前 Session 详情"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        return {}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        return True

    def execute(self, **kwargs) -> Dict:
        """Execute view session"""
        session_manager = kwargs.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {"status": "error"}

        session = session_manager.get_current_session()
        if not session:
            print_warning("当前没有活跃的 Session")
            return {"status": "no_session"}

        # Display session details
        print_info("\n" + "=" * 60)
        print_info("当前 Session 详情")
        print_info("=" * 60 + "\n")

        print(f"Session ID: {Colors.highlight(session.session_id)}")
        print(f"状态: {self._format_status(session.status)}")
        print(f"创建时间: {self._format_datetime(session.created_at)}")
        print(f"最后活动: {self._format_datetime(session.last_active_at)}")
        print(f"工作目录: {session.working_directory}")
        print(f"操作数: {session.get_command_count()}")
        print(f"持续时间: {self._format_duration(session.get_duration())}")

        # Show context
        if session.context:
            print(f"\n{Colors.BOLD}上下文数据:{Colors.RESET}")
            for key, value in session.context.items():
                print(f"  {key}: {value}")

        # Show metadata
        if session.metadata:
            print(f"\n{Colors.BOLD}元数据:{Colors.RESET}")
            for key, value in session.metadata.items():
                print(f"  {key}: {value}")

        print()

        return {"status": "success", "session_id": session.session_id}

    def _format_status(self, status: str) -> str:
        """Format status with color"""
        status_colors = {"active": Colors.GREEN, "paused": Colors.YELLOW, "completed": Colors.DIM}
        color = status_colors.get(status, Colors.RESET)
        return f"{color}{status}{Colors.RESET}"

    def _format_datetime(self, dt_str: str) -> str:
        """Format datetime string"""
        try:
            dt = datetime.fromisoformat(dt_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return dt_str

    def _format_duration(self, seconds: float) -> str:
        """Format duration"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours}h {minutes}m {secs}s"
        elif minutes > 0:
            return f"{minutes}m {secs}s"
        else:
            return f"{secs}s"


class SessionHistoryCommand(BaseCommand):
    """View session history"""

    name = "session_history"
    description = "查看操作历史"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        limit = self.prompt_text("显示最近几条记录 (默认: 10)", default="10")

        try:
            limit = int(limit)
        except ValueError:
            limit = 10

        return {"limit": limit}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        return True

    def execute(self, limit: int = 10, **kwargs) -> Dict:
        """Execute view history"""
        session_manager = kwargs.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {"status": "error"}

        history = session_manager.get_history(limit=limit)

        if not history:
            print_info("暂无操作历史")
            return {"status": "empty"}

        # Display history
        print_info("\n" + "=" * 60)
        print_info(f"操作历史 (最近 {len(history)} 条)")
        print_info("=" * 60 + "\n")

        for i, entry in enumerate(reversed(history), 1):
            timestamp = entry.get("timestamp", "")
            command = entry.get("command", "")
            params = entry.get("params", {})
            result = entry.get("result", {})
            duration = entry.get("duration", 0.0)

            # Format timestamp
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%H:%M:%S")
            except:
                time_str = timestamp

            # Format status
            status = result.get("status", "unknown")
            status_icon = "✅" if status == "success" else "❌"

            print(f"{i}. [{time_str}] {Colors.highlight(command)} ({duration:.2f}s)")

            # Show key parameters
            if params:
                key_params = {
                    k: v for k, v in params.items() if k in ["md_file", "bib_file", "output_file"]
                }
                if key_params:
                    for k, v in key_params.items():
                        if isinstance(v, str) and len(v) > 50:
                            v = "..." + v[-47:]
                        print(f"   {k}: {v}")

            # Show result
            print(f"   结果: {status_icon} {status}")
            if "count" in result:
                print(f"   数量: {result['count']}")

            print()

        return {"status": "success", "count": len(history)}


class SessionListCommand(BaseCommand):
    """List all sessions"""

    name = "session_list"
    description = "列出所有 Session"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        limit = self.prompt_text("显示最近几个 Session (默认: 20)", default="20")

        try:
            limit = int(limit)
        except ValueError:
            limit = 20

        return {"limit": limit}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        return True

    def execute(self, limit: int = 20, **kwargs) -> Dict:
        """Execute list sessions"""
        session_manager = kwargs.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {"status": "error"}

        sessions = session_manager.list_sessions(limit=limit)

        if not sessions:
            print_info("暂无 Session 记录")
            return {"status": "empty"}

        # Display sessions
        print_info("\n" + "=" * 60)
        print_info(f"Session 列表 (共 {len(sessions)} 个)")
        print_info("=" * 60 + "\n")

        current_session = session_manager.get_current_session()
        current_id = current_session.session_id if current_session else None

        for i, session in enumerate(sessions, 1):
            is_current = session.session_id == current_id
            marker = "▶" if is_current else " "

            # Format datetime
            try:
                dt = datetime.fromisoformat(session.last_active_at)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = session.last_active_at

            # Format status
            status_icon = {"active": "🟢", "paused": "🟡", "completed": "⚪"}.get(
                session.status, "❓"
            )

            print(f"{marker} {i}. {status_icon} {session.session_id}")
            print(
                f"     最后活动: {time_str} | 操作数: {session.get_command_count()} | 持续: {self._format_duration(session.get_duration())}"
            )
            if session.get_last_command():
                print(f"     最后命令: {session.get_last_command()}")
            print()

        return {"status": "success", "count": len(sessions)}

    def _format_duration(self, seconds: float) -> str:
        """Format duration"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{int(seconds)}s"


class SessionResumeCommand(BaseCommand):
    """Resume a session"""

    name = "session_resume"
    description = "恢复历史 Session"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        session_manager = context.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {}

        # List recent sessions
        sessions = session_manager.list_sessions(limit=10)
        if not sessions:
            print_info("暂无可恢复的 Session")
            return {}

        print_info("\n可恢复的 Session:\n")
        for i, session in enumerate(sessions, 1):
            try:
                dt = datetime.fromisoformat(session.last_active_at)
                time_str = dt.strftime("%Y-%m-%d %H:%M")
            except:
                time_str = session.last_active_at

            print(f"  {i}. {session.session_id} ({time_str})")

        choice = self.prompt_choice(
            f"选择要恢复的 Session (1-{len(sessions)})",
            [str(i) for i in range(1, len(sessions) + 1)],
        )

        idx = int(choice) - 1
        session_id = sessions[idx].session_id

        return {"session_id": session_id}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        session_id = kwargs.get("session_id")
        if not session_id:
            print_error("未指定 Session ID")
            return False
        return True

    def execute(self, session_id: str, **kwargs) -> Dict:
        """Execute resume session"""
        session_manager = kwargs.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {"status": "error"}

        session = session_manager.resume_session(session_id)
        if not session:
            print_error(f"无法恢复 Session: {session_id}")
            return {"status": "not_found"}

        print_success(f"已恢复 Session: {session_id}")
        print_info(f"工作目录: {session.working_directory}")
        print_info(f"操作数: {session.get_command_count()}")

        return {"status": "success", "session_id": session_id}


class SessionCleanupCommand(BaseCommand):
    """Cleanup old sessions"""

    name = "session_cleanup"
    description = "清理旧 Session"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        days = self.prompt_text("删除多少天前的 Session (默认: 30)", default="30")

        try:
            days = int(days)
        except ValueError:
            days = 30

        return {"days": days}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        return True

    def execute(self, days: int = 30, **kwargs) -> Dict:
        """Execute cleanup"""
        session_manager = kwargs.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {"status": "error"}

        print_info(f"\n正在清理 {days} 天前的 Session...")

        deleted_count = session_manager.cleanup_old_sessions(days=days)

        if deleted_count > 0:
            print_success(f"已删除 {deleted_count} 个旧 Session")
        else:
            print_info("没有需要清理的 Session")

        return {"status": "success", "deleted_count": deleted_count}


class SessionExportCommand(BaseCommand):
    """Export session"""

    name = "session_export"
    description = "导出 Session"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        session_manager = context.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {}

        current_session = session_manager.get_current_session()
        default_id = current_session.session_id if current_session else ""

        session_id = self.prompt_text(f"Session ID (默认: 当前 Session)", default=default_id)

        default_output = f"./{session_id}.json"
        output_file = self.prompt_text(
            f"输出文件路径 (默认: {default_output})", default=default_output
        )

        return {"session_id": session_id, "output_file": output_file}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        session_id = kwargs.get("session_id")
        if not session_id:
            print_error("未指定 Session ID")
            return False
        return True

    def execute(self, session_id: str, output_file: str, **kwargs) -> Dict:
        """Execute export"""
        session_manager = kwargs.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {"status": "error"}

        print_info(f"\n正在导出 Session: {session_id}")

        success = session_manager.export_session(session_id, output_file)

        if success:
            print_success(f"Session 已导出到: {output_file}")
            return {"status": "success", "output_file": output_file}
        else:
            print_error("导出失败")
            return {"status": "error"}


class SessionStatsCommand(BaseCommand):
    """Show session statistics"""

    name = "session_stats"
    description = "查看 Session 统计"

    def get_interactive_params(self, context) -> Dict:
        """Get parameters interactively"""
        return {}

    def validate(self, **kwargs) -> bool:
        """Validate parameters"""
        return True

    def execute(self, **kwargs) -> Dict:
        """Execute stats"""
        session_manager = kwargs.get("session_manager")
        if not session_manager:
            print_error("Session 管理器未初始化")
            return {"status": "error"}

        stats = session_manager.get_statistics()

        # Display statistics
        print_info("\n" + "=" * 60)
        print_info("Session 统计")
        print_info("=" * 60 + "\n")

        print(f"总 Session 数: {stats['total_sessions']}")
        print(f"活跃 Session 数: {stats['active_sessions']}")
        print(f"总操作数: {stats['total_commands']}")
        print(f"总持续时间: {self._format_duration(stats['total_duration'])}")
        print(f"存储大小: {self._format_size(stats['storage_size'])}")

        print()

        return {"status": "success", "stats": stats}

    def _format_duration(self, seconds: float) -> str:
        """Format duration"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        elif minutes > 0:
            return f"{minutes}m"
        else:
            return f"{int(seconds)}s"

    def _format_size(self, bytes: int) -> str:
        """Format file size"""
        for unit in ["B", "KB", "MB", "GB"]:
            if bytes < 1024.0:
                return f"{bytes:.2f} {unit}"
            bytes /= 1024.0
        return f"{bytes:.2f} TB"
