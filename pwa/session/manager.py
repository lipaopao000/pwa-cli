"""
Session manager
"""

import os
import time
from typing import Optional, Dict, Any, List
from pathlib import Path

from .models import Session, create_new_session
from .storage import SessionStorage


class SessionManager:
    """Session manager"""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize session manager
        
        Args:
            storage_dir: Directory to store sessions (default: ~/.config/pwa/sessions)
        """
        if storage_dir is None:
            storage_dir = Path.home() / ".config" / "pwa" / "sessions"
        
        self.storage = SessionStorage(str(storage_dir))
        self.current_session: Optional[Session] = None
        self._command_start_time: Optional[float] = None
    
    def start_session(self, working_directory: Optional[str] = None,
                     resume_last: bool = True) -> Session:
        """
        Start a new session or resume the last one
        
        Args:
            working_directory: Working directory for the session
            resume_last: Try to resume the last active session
            
        Returns:
            Session instance
        """
        if resume_last:
            # Try to resume the last active session
            last_session = self.storage.get_latest()
            if last_session and last_session.is_active():
                self.current_session = last_session
                self.current_session.mark_active()
                self.storage.save(self.current_session)
                return self.current_session
        
        # Create new session
        self.current_session = create_new_session(working_directory)
        self.storage.save(self.current_session)
        return self.current_session
    
    def get_current_session(self) -> Optional[Session]:
        """Get current session"""
        return self.current_session
    
    def save_current_session(self):
        """Save current session"""
        if self.current_session:
            self.storage.save(self.current_session)
    
    def end_session(self):
        """End current session"""
        if self.current_session:
            self.current_session.mark_completed()
            self.storage.save(self.current_session)
            self.current_session = None
    
    def pause_session(self):
        """Pause current session"""
        if self.current_session:
            self.current_session.mark_paused()
            self.storage.save(self.current_session)
    
    def resume_session(self, session_id: str) -> Optional[Session]:
        """
        Resume a session
        
        Args:
            session_id: Session ID to resume
            
        Returns:
            Resumed session or None
        """
        session = self.storage.load(session_id)
        if session:
            session.mark_active()
            self.current_session = session
            self.storage.save(session)
        return session
    
    def list_sessions(self, limit: Optional[int] = None) -> List[Session]:
        """
        List all sessions
        
        Args:
            limit: Maximum number of sessions to return
            
        Returns:
            List of sessions
        """
        return self.storage.list_all(limit=limit)
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session
        
        Args:
            session_id: Session ID to delete
            
        Returns:
            True if deleted successfully
        """
        return self.storage.delete(session_id)
    
    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Cleanup old sessions
        
        Args:
            days: Delete sessions older than this many days
            
        Returns:
            Number of deleted sessions
        """
        return self.storage.cleanup_old_sessions(days=days)
    
    # Context management
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value from current session"""
        if self.current_session:
            return self.current_session.get_context(key, default)
        return default
    
    def set_context(self, key: str, value: Any):
        """Set context value in current session"""
        if self.current_session:
            self.current_session.set_context(key, value)
            self.storage.save(self.current_session)
    
    def update_context(self, updates: Dict[str, Any]):
        """Update multiple context values"""
        if self.current_session:
            self.current_session.update_context(updates)
            self.storage.save(self.current_session)
    
    # History management
    
    def start_command(self):
        """Mark the start of a command execution"""
        self._command_start_time = time.time()
    
    def end_command(self, command: str, params: Dict[str, Any], 
                   result: Dict[str, Any]):
        """
        Record command execution
        
        Args:
            command: Command name
            params: Command parameters
            result: Command result
        """
        duration = 0.0
        if self._command_start_time:
            duration = time.time() - self._command_start_time
            self._command_start_time = None
        
        if self.current_session:
            self.current_session.add_history(command, params, result, duration)
            self.storage.save(self.current_session)
    
    def get_history(self, limit: Optional[int] = None) -> List[Dict]:
        """
        Get command history from current session
        
        Args:
            limit: Maximum number of history entries to return
            
        Returns:
            List of history entries
        """
        if self.current_session:
            history = self.current_session.history
            if limit:
                history = history[-limit:]
            return history
        return []
    
    def get_last_command(self) -> Optional[str]:
        """Get last executed command"""
        if self.current_session:
            return self.current_session.get_last_command()
        return None
    
    # Smart defaults
    
    def suggest_file_path(self, key: str) -> Optional[str]:
        """
        Suggest file path based on context
        
        Args:
            key: Context key (e.g., 'last_md_file', 'last_bib_file')
            
        Returns:
            Suggested file path or None
        """
        path = self.get_context(key)
        if path and os.path.exists(path):
            return path
        return None
    
    def suggest_config(self, key: str) -> Any:
        """
        Suggest configuration based on context
        
        Args:
            key: Context key (e.g., 'last_config')
            
        Returns:
            Suggested configuration or None
        """
        return self.get_context(key)
    
    # Export/Import
    
    def export_session(self, session_id: str, output_path: str) -> bool:
        """
        Export session to file
        
        Args:
            session_id: Session ID to export
            output_path: Output file path
            
        Returns:
            True if exported successfully
        """
        return self.storage.export_session(session_id, output_path)
    
    def import_session(self, input_path: str) -> Optional[Session]:
        """
        Import session from file
        
        Args:
            input_path: Input file path
            
        Returns:
            Imported session or None
        """
        return self.storage.import_session(input_path)
    
    # Statistics
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get session statistics"""
        all_sessions = self.storage.list_all()
        active_sessions = [s for s in all_sessions if s.is_active()]
        
        total_commands = sum(s.get_command_count() for s in all_sessions)
        total_duration = sum(s.get_duration() for s in all_sessions)
        
        return {
            "total_sessions": len(all_sessions),
            "active_sessions": len(active_sessions),
            "total_commands": total_commands,
            "total_duration": total_duration,
            "storage_size": self.storage.get_storage_size(),
        }
