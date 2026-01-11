"""
Session data models
"""

import os
import platform
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from enum import Enum


class SessionStatus(Enum):
    """Session status"""
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"


@dataclass
class HistoryEntry:
    """History entry for a command execution"""
    timestamp: str
    command: str
    params: Dict[str, Any]
    result: Dict[str, Any]
    duration: float = 0.0  # seconds
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'HistoryEntry':
        """Create from dictionary"""
        return cls(**data)


@dataclass
class Session:
    """Session data model"""
    
    session_id: str
    created_at: str
    last_active_at: str
    status: str = SessionStatus.ACTIVE.value
    working_directory: str = field(default_factory=os.getcwd)
    context: Dict[str, Any] = field(default_factory=dict)
    history: List[Dict] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post initialization"""
        if not self.metadata:
            self.metadata = self._create_metadata()
    
    def _create_metadata(self) -> Dict[str, Any]:
        """Create metadata"""
        from ..version import __version__
        
        return {
            "pwa_version": __version__,
            "python_version": platform.python_version(),
            "platform": platform.system(),
            "hostname": platform.node(),
        }
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Session':
        """Create from dictionary"""
        return cls(**data)
    
    def add_history(self, command: str, params: Dict[str, Any], 
                   result: Dict[str, Any], duration: float = 0.0):
        """Add history entry"""
        entry = HistoryEntry(
            timestamp=datetime.now().isoformat(),
            command=command,
            params=params,
            result=result,
            duration=duration
        )
        self.history.append(entry.to_dict())
        self.last_active_at = datetime.now().isoformat()
    
    def get_context(self, key: str, default: Any = None) -> Any:
        """Get context value"""
        return self.context.get(key, default)
    
    def set_context(self, key: str, value: Any):
        """Set context value"""
        self.context[key] = value
        self.last_active_at = datetime.now().isoformat()
    
    def update_context(self, updates: Dict[str, Any]):
        """Update multiple context values"""
        self.context.update(updates)
        self.last_active_at = datetime.now().isoformat()
    
    def get_last_command(self) -> Optional[str]:
        """Get last executed command"""
        if self.history:
            return self.history[-1]['command']
        return None
    
    def get_command_count(self) -> int:
        """Get total command count"""
        return len(self.history)
    
    def get_duration(self) -> float:
        """Get session duration in seconds"""
        created = datetime.fromisoformat(self.created_at)
        last_active = datetime.fromisoformat(self.last_active_at)
        return (last_active - created).total_seconds()
    
    def mark_completed(self):
        """Mark session as completed"""
        self.status = SessionStatus.COMPLETED.value
        self.last_active_at = datetime.now().isoformat()
    
    def mark_paused(self):
        """Mark session as paused"""
        self.status = SessionStatus.PAUSED.value
        self.last_active_at = datetime.now().isoformat()
    
    def mark_active(self):
        """Mark session as active"""
        self.status = SessionStatus.ACTIVE.value
        self.last_active_at = datetime.now().isoformat()
    
    def is_active(self) -> bool:
        """Check if session is active"""
        return self.status == SessionStatus.ACTIVE.value
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary"""
        return {
            "session_id": self.session_id,
            "status": self.status,
            "created_at": self.created_at,
            "last_active_at": self.last_active_at,
            "duration": self.get_duration(),
            "command_count": self.get_command_count(),
            "last_command": self.get_last_command(),
            "working_directory": self.working_directory,
        }


def create_session_id() -> str:
    """Create unique session ID"""
    from datetime import datetime
    import random
    import string
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"pwa_{timestamp}_{random_suffix}"


def create_new_session(working_directory: Optional[str] = None) -> Session:
    """Create a new session"""
    now = datetime.now().isoformat()
    
    return Session(
        session_id=create_session_id(),
        created_at=now,
        last_active_at=now,
        status=SessionStatus.ACTIVE.value,
        working_directory=working_directory or os.getcwd(),
        context={},
        history=[],
        metadata={}
    )
