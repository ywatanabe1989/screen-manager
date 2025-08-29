#!/usr/bin/env python3
"""
Unit tests for ScreenSessionManager functionality.

Tests session creation, status monitoring, exit code handling, and all
session management operations for Python processes in screen sessions.
"""

import os
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, mock_open, MagicMock
from datetime import datetime

import pytest

from screen_manager.screen_manager import ScreenSessionManager


@pytest.mark.unit
class TestScreenSessionManagerInit:
    """Test ScreenSessionManager initialization."""
    
    def test_init_default(self):
        """Test default initialization."""
        manager = ScreenSessionManager()
        
        assert hasattr(manager, 'agent_id')
        assert isinstance(manager.agent_id, str)
        assert len(manager.agent_id) > 0
        assert hasattr(manager, '_sessions')
        assert isinstance(manager._sessions, dict)
    
    def test_init_with_agent_id(self):
        """Test initialization with specific agent ID."""
        test_agent_id = "test-agent-123"
        manager = ScreenSessionManager(agent_id=test_agent_id)
        
        assert manager.agent_id == test_agent_id
        assert manager._sessions == {}
    
    def test_init_uses_cipdb_get_agent_id(self):
        """Test initialization uses cipdb.get_agent_id when no agent_id provided."""
        with patch('screen_manager.screen_manager.get_agent_id') as mock_get_agent:
            mock_get_agent.return_value = "mocked-agent-id"
            
            manager = ScreenSessionManager()
            
            mock_get_agent.assert_called_once()
            assert manager.agent_id == "mocked-agent-id"


@pytest.mark.unit
class TestCreateSession:
    """Test session creation functionality."""
    
    def test_create_session_success(self, mock_subprocess):
        """Test successful session creation."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Mock successful screen command
        mock_subprocess.return_value.returncode = 0
        
        result = manager.create_session(
            name="test-session",
            command="python -c 'print(\"hello\")'",
            working_dir="/tmp/test"
        )
        
        # Verify result
        assert result['success'] is True
        assert result['session_name'] == "test-agent-test-session"
        assert result['status'] == 'running'
        assert 'message' in result
        
        # Verify session was stored
        assert "test-agent-test-session" in manager._sessions
        session_info = manager._sessions["test-agent-test-session"]
        assert session_info['name'] == "test-agent-test-session"
        assert session_info['command'] == "python -c 'print(\"hello\")'"
        assert session_info['working_dir'] == "/tmp/test"
        assert session_info['agent_id'] == "test-agent"
        assert session_info['status'] == 'running'
        assert session_info['exit_code'] is None
    
    def test_create_session_default_working_dir(self, mock_subprocess):
        """Test session creation with default working directory."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.return_value.returncode = 0
        
        with patch('os.getcwd', return_value='/current/dir'):
            result = manager.create_session(
                name="test-session",
                command="python script.py"
            )
        
        assert result['success'] is True
        session_info = manager._sessions["test-agent-test-session"]
        assert session_info['working_dir'] == '/current/dir'
    
    def test_create_session_failure(self, mock_subprocess):
        """Test session creation failure."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Mock failed screen command
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=['screen'], stderr="Screen command failed"
        )
        
        result = manager.create_session(
            name="test-session",
            command="python script.py"
        )
        
        # Verify failure result
        assert result['success'] is False
        assert 'error' in result
        assert result['session_name'] == "test-agent-test-session"
        assert "test-agent-test-session" not in manager._sessions
    
    def test_create_session_command_wrapping(self, mock_subprocess):
        """Test that commands are properly wrapped with exit code capture."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.return_value.returncode = 0
        
        manager.create_session(
            name="test-session",
            command="python script.py",
            working_dir="/test/dir"
        )
        
        # Verify screen command was called with wrapped command
        call_args = mock_subprocess.call_args[0][0]
        assert 'screen' in call_args
        assert '-dmS' in call_args
        assert 'test-agent-test-session' in call_args
        
        # Check that exit code capture is added
        wrapped_command = call_args[-1]  # Last argument should be the command
        assert 'EXIT_CODE:$?' in wrapped_command
        assert '/tmp/test-agent-test-session.exit' in wrapped_command


@pytest.mark.unit  
class TestSessionStatus:
    """Test session status monitoring."""
    
    def test_get_session_status_running(self):
        """Test getting status of running session."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Add session to internal storage
        session_name = "test-agent-session"
        manager._sessions[session_name] = {
            'name': session_name,
            'command': 'python test.py',
            'working_dir': '/test',
            'created_at': datetime.now().isoformat(),
            'agent_id': 'test-agent',
            'status': 'running',
            'exit_code': None
        }
        
        with patch.object(manager, '_is_screen_session_running', return_value=True), \
             patch.object(manager, '_get_exit_code', return_value=None):
            
            status = manager.get_session_status("session")
            
            assert status['session_name'] == session_name
            assert status['status'] == 'running'
            assert status['exit_code'] is None
            assert status['is_running'] is True
            assert status['agent_id'] == 'test-agent'
            assert 'created_at' in status
            assert status['command'] == 'python test.py'
    
    def test_get_session_status_completed(self):
        """Test getting status of completed session."""
        manager = ScreenSessionManager(agent_id="test-agent")
        session_name = "test-agent-session"
        
        with patch.object(manager, '_is_screen_session_running', return_value=False), \
             patch.object(manager, '_get_exit_code', return_value=0):
            
            status = manager.get_session_status("session")
            
            assert status['session_name'] == session_name
            assert status['status'] == 'completed'
            assert status['exit_code'] == 0
            assert status['is_running'] is False
    
    def test_get_session_status_error(self):
        """Test getting status of session with error exit code."""
        manager = ScreenSessionManager(agent_id="test-agent")
        session_name = "test-agent-session"
        
        with patch.object(manager, '_is_screen_session_running', return_value=False), \
             patch.object(manager, '_get_exit_code', return_value=1):
            
            status = manager.get_session_status("session")
            
            assert status['session_name'] == session_name
            assert status['status'] == 'error'
            assert status['exit_code'] == 1
            assert status['is_running'] is False
    
    def test_get_session_status_unknown(self):
        """Test getting status of session in unknown state."""
        manager = ScreenSessionManager(agent_id="test-agent")
        session_name = "test-agent-session"
        
        with patch.object(manager, '_is_screen_session_running', return_value=False), \
             patch.object(manager, '_get_exit_code', return_value=None):
            
            status = manager.get_session_status("session")
            
            assert status['session_name'] == session_name
            assert status['status'] == 'unknown'
            assert status['exit_code'] is None
            assert status['is_running'] is False
    
    def test_normalize_session_name(self):
        """Test session name normalization."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Test name without prefix
        normalized = manager._normalize_session_name("session")
        assert normalized == "test-agent-session"
        
        # Test name with prefix already
        normalized = manager._normalize_session_name("test-agent-session")
        assert normalized == "test-agent-session"


@pytest.mark.unit
class TestExitCodeHandling:
    """Test exit code detection and handling."""
    
    def test_get_exit_code_success(self):
        """Test getting exit code for successful completion."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with patch.object(manager, '_get_exit_code', return_value=0):
            exit_code = manager.get_exit_code("session")
            assert exit_code == 0
    
    def test_get_exit_code_error(self):
        """Test getting exit code for error completion."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with patch.object(manager, '_get_exit_code', return_value=1):
            exit_code = manager.get_exit_code("session")
            assert exit_code == 1
    
    def test_get_exit_code_not_available(self):
        """Test getting exit code when not available."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with patch.object(manager, '_get_exit_code', return_value=None):
            exit_code = manager.get_exit_code("session")
            assert exit_code is None
    
    def test_get_exit_code_from_file(self):
        """Test reading exit code from file."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("EXIT_CODE:42\n")
            temp_file = f.name
        
        try:
            with patch('os.path.exists', return_value=True), \
                 patch('builtins.open', mock_open(read_data="EXIT_CODE:42\n")):
                
                exit_code = manager._get_exit_code("test-session")
                assert exit_code == 42
        finally:
            os.unlink(temp_file)
    
    def test_get_exit_code_invalid_format(self):
        """Test handling of invalid exit code file format."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="INVALID FORMAT\n")):
            
            exit_code = manager._get_exit_code("test-session")
            assert exit_code is None
    
    def test_get_exit_code_file_not_exists(self):
        """Test exit code when file doesn't exist."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with patch('os.path.exists', return_value=False):
            exit_code = manager._get_exit_code("test-session")
            assert exit_code is None


@pytest.mark.unit
class TestWaitForCompletion:
    """Test waiting for session completion."""
    
    def test_wait_for_completion_success(self):
        """Test successful wait for completion."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Mock status progression: running -> completed
        status_sequence = [
            {'status': 'running', 'exit_code': None},
            {'status': 'completed', 'exit_code': 0}
        ]
        
        with patch.object(manager, 'get_session_status', side_effect=status_sequence), \
             patch('time.sleep'):  # Speed up test
            
            result = manager.wait_for_completion("session", timeout=5)
            
            assert result['success'] is True
            assert result['status'] == 'completed'
            assert result['exit_code'] == 0
            assert 'duration' in result
    
    def test_wait_for_completion_error(self):
        """Test wait for completion with error exit."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Mock status progression: running -> error
        status_sequence = [
            {'status': 'running', 'exit_code': None},
            {'status': 'error', 'exit_code': 1}
        ]
        
        with patch.object(manager, 'get_session_status', side_effect=status_sequence), \
             patch('time.sleep'):
            
            result = manager.wait_for_completion("session", timeout=5)
            
            assert result['success'] is True
            assert result['status'] == 'error'
            assert result['exit_code'] == 1
    
    def test_wait_for_completion_timeout(self):
        """Test wait for completion timeout."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Mock session that never completes
        with patch.object(manager, 'get_session_status', 
                         return_value={'status': 'running', 'exit_code': None}), \
             patch('time.sleep'), \
             patch('time.time', side_effect=[0, 1, 2, 3, 4, 5, 6]):  # Simulate time progression
            
            result = manager.wait_for_completion("session", timeout=5)
            
            assert result['success'] is False
            assert result['status'] == 'timeout'
            assert result['exit_code'] is None
            assert result['duration'] == 5
            assert 'message' in result


@pytest.mark.unit
class TestSendCommand:
    """Test sending commands to running sessions."""
    
    def test_send_command_success(self, mock_subprocess):
        """Test successful command sending."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.return_value.returncode = 0
        
        with patch.object(manager, '_is_screen_session_running', return_value=True):
            result = manager.send_command("session", "print('hello')")
            
            assert result['success'] is True
            assert result['command'] == "print('hello')"
            assert 'message' in result
    
    def test_send_command_session_not_running(self):
        """Test sending command to non-running session."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with patch.object(manager, '_is_screen_session_running', return_value=False):
            result = manager.send_command("session", "print('hello')")
            
            assert result['success'] is False
            assert 'error' in result
            assert 'not running' in result['error']
    
    def test_send_command_screen_failure(self, mock_subprocess):
        """Test command sending with screen failure."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=['screen'], stderr="Failed to send command"
        )
        
        with patch.object(manager, '_is_screen_session_running', return_value=True):
            result = manager.send_command("session", "print('hello')")
            
            assert result['success'] is False
            assert 'error' in result


@pytest.mark.unit
class TestGetOutput:
    """Test getting session output."""
    
    def test_get_output_success(self, mock_subprocess):
        """Test successful output retrieval."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.return_value.returncode = 0
        
        sample_output = "Line 1\nLine 2\nLine 3\n"
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=sample_output)):
            
            output = manager.get_output("session", lines=3)
            
            assert output == sample_output
    
    def test_get_output_limit_lines(self):
        """Test output retrieval with line limit."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        sample_lines = [f"Line {i}\n" for i in range(10)]
        sample_output = ''.join(sample_lines)
        
        with patch('subprocess.run'), \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data=sample_output)):
            
            output = manager.get_output("session", lines=3)
            
            # Should get last 3 lines
            expected = ''.join(sample_lines[-3:])
            assert output == expected
    
    def test_get_output_file_not_exists(self, mock_subprocess):
        """Test output retrieval when file doesn't exist."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.return_value.returncode = 0
        
        with patch('os.path.exists', return_value=False):
            output = manager.get_output("session")
            
            assert output == "No output available"
    
    def test_get_output_exception(self, mock_subprocess):
        """Test output retrieval with exception."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.side_effect = Exception("Test error")
        
        output = manager.get_output("session")
        
        assert "Error reading output" in output
        assert "Test error" in output


@pytest.mark.unit
class TestSessionCleanup:
    """Test session cleanup functionality."""
    
    def test_cleanup_session_success(self, mock_subprocess):
        """Test successful session cleanup."""
        manager = ScreenSessionManager(agent_id="test-agent")
        session_name = "test-agent-session"
        
        # Add session to internal storage
        manager._sessions[session_name] = {'name': session_name}
        
        mock_subprocess.return_value.returncode = 0
        
        with patch.object(manager, '_is_screen_session_running', return_value=True), \
             patch('os.path.exists', return_value=True), \
             patch('os.remove') as mock_remove:
            
            result = manager.cleanup_session("session")
            
            assert result is True
            assert session_name not in manager._sessions
            
            # Verify temp files were removed
            assert mock_remove.call_count >= 2  # .exit and .out files
    
    def test_cleanup_session_not_running(self, mock_subprocess):
        """Test cleanup of non-running session."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.return_value.returncode = 0
        
        with patch.object(manager, '_is_screen_session_running', return_value=False), \
             patch('os.path.exists', return_value=False):
            
            result = manager.cleanup_session("session")
            
            assert result is True
    
    def test_cleanup_session_exception(self):
        """Test cleanup with exception."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with patch.object(manager, '_is_screen_session_running', side_effect=Exception("Test error")):
            result = manager.cleanup_session("session")
            
            assert result is False


@pytest.mark.unit
class TestListSessions:
    """Test session listing functionality."""
    
    def test_list_sessions_success(self, mock_subprocess):
        """Test successful session listing."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Mock screen -ls output
        screen_output = "There are screens on:\n\t12345.test-agent-session1\t(Detached)\n\t12346.test-agent-session2\t(Attached)\n"
        mock_subprocess.return_value.stdout = screen_output
        mock_subprocess.return_value.returncode = 0
        
        with patch.object(manager, 'get_session_status') as mock_status:
            mock_status.side_effect = [
                {'session_name': 'test-agent-session1', 'status': 'running', 'exit_code': None},
                {'session_name': 'test-agent-session2', 'status': 'completed', 'exit_code': 0}
            ]
            
            sessions = manager.list_sessions()
            
            assert len(sessions) == 2
            assert sessions[0]['session_name'] == 'test-agent-session1'
            assert sessions[1]['session_name'] == 'test-agent-session2'
    
    def test_list_sessions_no_sessions(self, mock_subprocess):
        """Test listing sessions when none exist."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=['screen', '-ls']
        )
        
        sessions = manager.list_sessions()
        
        assert sessions == []
    
    def test_parse_screen_list(self):
        """Test parsing screen -ls output."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        screen_output = """There are screens on:
        12345.test-agent-session1	(Detached)
        12346.other-agent-session	(Attached)
        12347.test-agent-session2	(Detached)
2 Sockets in /tmp/screens/S-user."""
        
        sessions = manager._parse_screen_list(screen_output)
        
        assert 'test-agent-session1' in sessions
        assert 'other-agent-session' in sessions
        assert 'test-agent-session2' in sessions
        assert len(sessions) == 3


@pytest.mark.unit
class TestScreenSessionHelpers:
    """Test helper methods for screen session management."""
    
    def test_is_screen_session_running_true(self, mock_subprocess):
        """Test detecting running screen session."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        screen_output = "There are screens on:\n\t12345.test-agent-session\t(Detached)\n"
        mock_subprocess.return_value.stdout = screen_output
        mock_subprocess.return_value.returncode = 0
        
        is_running = manager._is_screen_session_running("test-agent-session")
        
        assert is_running is True
    
    def test_is_screen_session_running_false(self, mock_subprocess):
        """Test detecting non-running screen session."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        mock_subprocess.return_value.stdout = "No Sockets found in /tmp/screens/S-user.\n"
        mock_subprocess.return_value.returncode = 1
        
        is_running = manager._is_screen_session_running("test-agent-session")
        
        assert is_running is False
    
    def test_is_screen_session_running_exception(self, mock_subprocess):
        """Test screen session detection with exception."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        mock_subprocess.side_effect = subprocess.CalledProcessError(
            returncode=1, cmd=['screen', '-ls']
        )
        
        is_running = manager._is_screen_session_running("test-agent-session")
        
        assert is_running is False


@pytest.mark.unit
@pytest.mark.performance
class TestPerformance:
    """Test performance requirements for ScreenSessionManager."""
    
    def test_session_status_performance(self, performance_threshold):
        """Test session status check performance."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        with patch.object(manager, '_is_screen_session_running', return_value=True), \
             patch.object(manager, '_get_exit_code', return_value=None):
            
            start_time = time.time()
            manager.get_session_status("session")
            duration = time.time() - start_time
            
            assert duration < performance_threshold['session_status_check']
    
    def test_session_creation_performance(self, performance_threshold, mock_subprocess):
        """Test session creation performance."""
        manager = ScreenSessionManager(agent_id="test-agent")
        mock_subprocess.return_value.returncode = 0
        
        start_time = time.time()
        manager.create_session("session", "python -c 'print(\"test\")'")
        duration = time.time() - start_time
        
        assert duration < performance_threshold['session_creation']


if __name__ == "__main__":
    # Import subprocess here to avoid issues during test collection
    import subprocess
    print("Running ScreenSessionManager unit tests...")
    pytest.main([__file__, "-v"])