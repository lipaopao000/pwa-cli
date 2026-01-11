"""
Tests for session models
"""

import pytest
from datetime import datetime
from pwa.session.models import Session, create_session_id, create_new_session, SessionStatus


class TestSession:
    """Test Session model"""
    
    def test_create_session_id(self):
        """Test session ID creation"""
        session_id = create_session_id()
        assert session_id.startswith("pwa_")
        assert len(session_id) > 20
    
    def test_create_new_session(self):
        """Test new session creation"""
        session = create_new_session()
        assert session.session_id.startswith("pwa_")
        assert session.status == SessionStatus.ACTIVE.value
        assert isinstance(session.context, dict)
        assert isinstance(session.history, list)
        assert isinstance(session.metadata, dict)
    
    def test_session_to_dict(self):
        """Test session to dictionary conversion"""
        session = create_new_session()
        data = session.to_dict()
        assert isinstance(data, dict)
        assert 'session_id' in data
        assert 'created_at' in data
        assert 'status' in data
    
    def test_session_from_dict(self):
        """Test session from dictionary creation"""
        session = create_new_session()
        data = session.to_dict()
        restored = Session.from_dict(data)
        assert restored.session_id == session.session_id
        assert restored.status == session.status
    
    def test_add_history(self):
        """Test adding history entry"""
        session = create_new_session()
        session.add_history(
            command="test_command",
            params={"param1": "value1"},
            result={"status": "success"},
            duration=1.5
        )
        assert len(session.history) == 1
        assert session.history[0]['command'] == "test_command"
        assert session.history[0]['duration'] == 1.5
    
    def test_context_operations(self):
        """Test context operations"""
        session = create_new_session()
        
        # Set context
        session.set_context("key1", "value1")
        assert session.get_context("key1") == "value1"
        
        # Get with default
        assert session.get_context("nonexistent", "default") == "default"
        
        # Update context
        session.update_context({"key2": "value2", "key3": "value3"})
        assert session.get_context("key2") == "value2"
        assert session.get_context("key3") == "value3"
    
    def test_status_operations(self):
        """Test status operations"""
        session = create_new_session()
        
        assert session.is_active()
        
        session.mark_paused()
        assert session.status == SessionStatus.PAUSED.value
        assert not session.is_active()
        
        session.mark_completed()
        assert session.status == SessionStatus.COMPLETED.value
        
        session.mark_active()
        assert session.is_active()
    
    def test_get_summary(self):
        """Test get summary"""
        session = create_new_session()
        session.add_history(
            command="test_command",
            params={},
            result={"status": "success"}
        )
        
        summary = session.get_summary()
        assert isinstance(summary, dict)
        assert 'session_id' in summary
        assert 'command_count' in summary
        assert summary['command_count'] == 1
        assert summary['last_command'] == "test_command"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
