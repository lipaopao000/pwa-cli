"""
Session storage
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional

from .models import Session


class SessionStorage:
    """Session storage manager"""

    def __init__(self, storage_dir: str):
        """
        Initialize session storage

        Args:
            storage_dir: Directory to store session files
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save(self, session: Session):
        """
        Save session to file

        Args:
            session: Session to save
        """
        file_path = self._get_session_path(session.session_id)

        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)

    def load(self, session_id: str) -> Optional[Session]:
        """
        Load session from file

        Args:
            session_id: Session ID to load

        Returns:
            Session instance or None if not found
        """
        file_path = self._get_session_path(session_id)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Session.from_dict(data)
        except Exception:
            return None

    def exists(self, session_id: str) -> bool:
        """
        Check if session exists

        Args:
            session_id: Session ID to check

        Returns:
            True if session exists
        """
        return self._get_session_path(session_id).exists()

    def delete(self, session_id: str) -> bool:
        """
        Delete session file

        Args:
            session_id: Session ID to delete

        Returns:
            True if deleted successfully
        """
        file_path = self._get_session_path(session_id)

        if file_path.exists():
            try:
                file_path.unlink()
                return True
            except Exception:
                return False

        return False

    def list_all(self, limit: Optional[int] = None) -> List[Session]:
        """
        List all sessions

        Args:
            limit: Maximum number of sessions to return

        Returns:
            List of sessions sorted by last_active_at (newest first)
        """
        sessions = []

        for file_path in self.storage_dir.glob("pwa_*.json"):
            try:
                session = self.load(file_path.stem)
                if session:
                    sessions.append(session)
            except Exception:
                pass

        # Sort by last_active_at (newest first)
        sessions.sort(key=lambda s: datetime.fromisoformat(s.last_active_at), reverse=True)

        if limit:
            sessions = sessions[:limit]

        return sessions

    def list_active(self) -> List[Session]:
        """
        List active sessions

        Returns:
            List of active sessions
        """
        all_sessions = self.list_all()
        return [s for s in all_sessions if s.is_active()]

    def get_latest(self) -> Optional[Session]:
        """
        Get the most recent session

        Returns:
            Latest session or None
        """
        sessions = self.list_all(limit=1)
        return sessions[0] if sessions else None

    def cleanup_old_sessions(self, days: int = 30) -> int:
        """
        Delete sessions older than specified days

        Args:
            days: Number of days to keep

        Returns:
            Number of deleted sessions
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        deleted_count = 0

        for session in self.list_all():
            last_active = datetime.fromisoformat(session.last_active_at)

            if last_active < cutoff_date:
                if self.delete(session.session_id):
                    deleted_count += 1

        return deleted_count

    def get_storage_size(self) -> int:
        """
        Get total storage size in bytes

        Returns:
            Total size in bytes
        """
        total_size = 0

        for file_path in self.storage_dir.glob("pwa_*.json"):
            try:
                total_size += file_path.stat().st_size
            except Exception:
                pass

        return total_size

    def _get_session_path(self, session_id: str) -> Path:
        """Get session file path"""
        return self.storage_dir / f"{session_id}.json"

    def export_session(self, session_id: str, output_path: str) -> bool:
        """
        Export session to a file

        Args:
            session_id: Session ID to export
            output_path: Output file path

        Returns:
            True if exported successfully
        """
        session = self.load(session_id)
        if not session:
            return False

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            return True
        except Exception:
            return False

    def import_session(self, input_path: str) -> Optional[Session]:
        """
        Import session from a file

        Args:
            input_path: Input file path

        Returns:
            Imported session or None
        """
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            session = Session.from_dict(data)
            self.save(session)
            return session
        except Exception:
            return None
