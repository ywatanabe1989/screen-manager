#!/usr/bin/env python3
"""
Mock utilities for testing screen session functionality without actual screen dependency.

Provides realistic mock implementations that simulate screen command behavior,
session state management, and file system interactions for comprehensive testing.
"""

import os
import time
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from unittest.mock import Mock, MagicMock, mock_open
from datetime import datetime


class MockScreenSession:
    """Mock implementation of a screen session."""
    
    def __init__(self, name: str, command: str, working_dir: Optional[str] = None):
        self.name = name
        self.command = command
        self.working_dir = working_dir or os.getcwd()
        self.created_at = datetime.now()
        self.status = 'running'
        self.exit_code: Optional[int] = None
        self.output_buffer = []
        self.is_attached = False
        self.pid = 12345  # Mock PID
        
        # Simulate initial output
        self.output_buffer.extend([
            f"Session {name} created",
            f"Executing: {command}",
            f"Working directory: {working_dir}"
        ])
    
    def send_command(self, command: str) -> bool:
        """Simulate sending a command to the session."""
        if self.status != 'running':
            return False
        
        self.output_buffer.append(f">>> {command}")
        
        # Simulate command execution
        if 'exit' in command:
            self.complete(exit_code=0)
        elif 'error' in command:
            self.output_buffer.append("Error occurred")
            self.complete(exit_code=1)
        else:
            self.output_buffer.append(f"Executed: {command}")
        
        return True
    
    def complete(self, exit_code: int = 0) -> None:
        """Mark session as completed with exit code."""
        self.status = 'completed' if exit_code == 0 else 'error'
        self.exit_code = exit_code
        self.output_buffer.append(f"Session completed with exit code: {exit_code}")
    
    def get_output(self, lines: int = 20) -> str:
        """Get recent output from session."""
        recent_output = self.output_buffer[-lines:] if lines > 0 else self.output_buffer
        return '\n'.join(recent_output) + '\n'
    
    def is_running(self) -> bool:
        """Check if session is running."""
        return self.status == 'running'
    
    def get_info(self) -> Dict[str, Any]:
        """Get session information."""
        return {
            'name': self.name,
            'command': self.command,
            'working_dir': self.working_dir,
            'created_at': self.created_at.isoformat(),
            'status': self.status,
            'exit_code': self.exit_code,
            'is_running': self.is_running(),
            'pid': self.pid,
            'is_attached': self.is_attached
        }


class MockScreenManager:
    """Mock implementation of screen session management."""
    
    def __init__(self):
        self.sessions: Dict[str, MockScreenSession] = {}
        self.call_history: List[Dict[str, Any]] = []
        self.temp_files: Dict[str, str] = {}
    
    def create_session(self, name: str, command: str, working_dir: Optional[str] = None) -> MockScreenSession:
        """Create a new mock screen session."""
        self._log_call('create_session', {
            'name': name,
            'command': command,
            'working_dir': working_dir
        })
        
        session = MockScreenSession(name, command, working_dir)
        self.sessions[name] = session
        
        # Create mock exit file path
        exit_file_path = f"/tmp/{name}.exit"
        self.temp_files[exit_file_path] = ""
        
        return session
    
    def get_session(self, name: str) -> Optional[MockScreenSession]:
        """Get session by name."""
        self._log_call('get_session', {'name': name})
        return self.sessions.get(name)
    
    def list_sessions(self, filter_prefix: Optional[str] = None) -> List[str]:
        """List all session names, optionally filtered by prefix."""
        self._log_call('list_sessions', {'filter_prefix': filter_prefix})
        
        session_names = list(self.sessions.keys())
        
        if filter_prefix:
            session_names = [name for name in session_names if name.startswith(filter_prefix)]
        
        return session_names
    
    def send_command(self, name: str, command: str) -> bool:
        """Send command to session."""
        self._log_call('send_command', {'name': name, 'command': command})
        
        session = self.sessions.get(name)
        if not session:
            return False
        
        return session.send_command(command)
    
    def kill_session(self, name: str) -> bool:
        """Kill a session."""
        self._log_call('kill_session', {'name': name})
        
        if name in self.sessions:
            session = self.sessions[name]
            session.complete(exit_code=130)  # SIGINT exit code
            return True
        
        return False
    
    def cleanup_session(self, name: str) -> bool:
        """Clean up session and associated files."""
        self._log_call('cleanup_session', {'name': name})
        
        if name in self.sessions:
            del self.sessions[name]
            
            # Clean up temp files
            exit_file = f"/tmp/{name}.exit"
            output_file = f"/tmp/{name}.out"
            
            if exit_file in self.temp_files:
                del self.temp_files[exit_file]
            if output_file in self.temp_files:
                del self.temp_files[output_file]
            
            return True
        
        return False
    
    def simulate_completion(self, name: str, exit_code: int = 0, delay: float = 0.0) -> None:
        """Simulate session completion after delay."""
        if delay > 0:
            time.sleep(delay)
        
        session = self.sessions.get(name)
        if session:
            session.complete(exit_code)
            
            # Write exit code to mock file
            exit_file_path = f"/tmp/{name}.exit"
            self.temp_files[exit_file_path] = f"EXIT_CODE:{exit_code}\n"
    
    def get_screen_list_output(self) -> str:
        """Generate mock screen -ls output."""
        if not self.sessions:
            return "No Sockets found in /tmp/screens/S-user.\n"
        
        output_lines = ["There are screens on:"]
        
        for i, (name, session) in enumerate(self.sessions.items(), start=12345):
            status = "(Attached)" if session.is_attached else "(Detached)"
            output_lines.append(f"\t{i}.{name}\t{status}")
        
        socket_count = len(self.sessions)
        output_lines.append(f"{socket_count} Socket{'s' if socket_count != 1 else ''} in /tmp/screens/S-user.")
        
        return '\n'.join(output_lines) + '\n'
    
    def write_exit_code(self, session_name: str, exit_code: int) -> None:
        """Write exit code to mock file."""
        exit_file_path = f"/tmp/{session_name}.exit"
        self.temp_files[exit_file_path] = f"EXIT_CODE:{exit_code}\n"
    
    def write_output(self, session_name: str, output: str) -> None:
        """Write output to mock file."""
        output_file_path = f"/tmp/{session_name}.out"
        self.temp_files[output_file_path] = output
    
    def _log_call(self, method: str, args: Dict[str, Any]) -> None:
        """Log method calls for testing verification."""
        self.call_history.append({
            'method': method,
            'args': args,
            'timestamp': datetime.now().isoformat()
        })
    
    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of method calls."""
        return self.call_history.copy()
    
    def clear_call_history(self) -> None:
        """Clear call history."""
        self.call_history.clear()


class ScreenMockContext:
    """Context manager for mocking screen operations."""
    
    def __init__(self, mock_manager: Optional[MockScreenManager] = None):
        self.mock_manager = mock_manager or MockScreenManager()
        self.original_patches = []
    
    def __enter__(self) -> MockScreenManager:
        """Set up screen mocking."""
        import subprocess
        from unittest.mock import patch
        
        def mock_subprocess_run(cmd, *args, **kwargs):
            """Mock subprocess.run for screen commands."""
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            
            if not isinstance(cmd, list):
                return result
            
            if 'screen' not in cmd[0]:
                return result
            
            # Handle different screen commands
            if '-dmS' in cmd:
                # Create session: screen -dmS session_name command
                session_name = cmd[cmd.index('-dmS') + 1]
                command = ' '.join(cmd[3:]) if len(cmd) > 3 else 'bash'
                self.mock_manager.create_session(session_name, command)
                
            elif '-ls' in cmd:
                # List sessions: screen -ls
                result.stdout = self.mock_manager.get_screen_list_output()
                result.returncode = 0 if self.mock_manager.sessions else 1
                
            elif '-S' in cmd and 'stuff' in cmd:
                # Send command: screen -S session_name -p 0 -X stuff 'command\n'
                session_name = cmd[cmd.index('-S') + 1]
                if 'stuff' in cmd:
                    stuff_index = cmd.index('stuff')
                    if stuff_index + 1 < len(cmd):
                        command = cmd[stuff_index + 1].replace('\\n', '').replace('\n', '')
                        success = self.mock_manager.send_command(session_name, command)
                        result.returncode = 0 if success else 1
                
            elif '-S' in cmd and 'hardcopy' in cmd:
                # Capture output: screen -S session_name -p 0 -X hardcopy /path/to/file
                session_name = cmd[cmd.index('-S') + 1]
                if 'hardcopy' in cmd:
                    hardcopy_index = cmd.index('hardcopy')
                    if hardcopy_index + 1 < len(cmd):
                        output_file = cmd[hardcopy_index + 1]
                        session = self.mock_manager.get_session(session_name)
                        if session:
                            output_content = session.get_output()
                            self.mock_manager.temp_files[output_file] = output_content
                
            elif '-S' in cmd and 'quit' in cmd:
                # Kill session: screen -S session_name -X quit
                session_name = cmd[cmd.index('-S') + 1]
                success = self.mock_manager.kill_session(session_name)
                result.returncode = 0 if success else 1
            
            elif '--version' in cmd:
                # Version check: screen --version
                result.stdout = "Screen version 4.09.00 (GNU) 30-Jan-22"
                result.returncode = 0
            
            return result
        
        def mock_os_path_exists(path):
            """Mock os.path.exists for temp files."""
            return path in self.mock_manager.temp_files
        
        def mock_open_file(filename, mode='r'):
            """Mock file opening for temp files."""
            if filename in self.mock_manager.temp_files:
                content = self.mock_manager.temp_files[filename]
                return mock_open(read_data=content)()
            else:
                raise FileNotFoundError(f"No such file: {filename}")
        
        # Apply patches
        self.subprocess_patch = patch('subprocess.run', side_effect=mock_subprocess_run)
        self.os_exists_patch = patch('os.path.exists', side_effect=mock_os_path_exists)
        self.builtins_open_patch = patch('builtins.open', side_effect=mock_open_file)
        
        self.subprocess_patch.start()
        self.os_exists_patch.start()
        self.builtins_open_patch.start()
        
        return self.mock_manager
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up screen mocking."""
        self.subprocess_patch.stop()
        self.os_exists_patch.stop()
        self.builtins_open_patch.stop()


def create_mock_screen_environment() -> ScreenMockContext:
    """Create a complete mock screen environment for testing."""
    return ScreenMockContext()


def create_session_with_progression(
    mock_manager: MockScreenManager,
    name: str,
    command: str,
    progression: List[Dict[str, Any]]
) -> MockScreenSession:
    """
    Create a session that follows a specific progression pattern.
    
    Args:
        mock_manager: Mock screen manager
        name: Session name
        command: Command to run
        progression: List of states with timing, e.g.:
            [
                {'delay': 0.0, 'status': 'running'},
                {'delay': 1.0, 'command': 'print("test")'},
                {'delay': 2.0, 'exit_code': 0}
            ]
    
    Returns:
        Created mock session
    """
    session = mock_manager.create_session(name, command)
    
    def apply_progression():
        for step in progression:
            if 'delay' in step:
                time.sleep(step['delay'])
            
            if 'command' in step:
                session.send_command(step['command'])
            
            if 'exit_code' in step:
                session.complete(step['exit_code'])
                mock_manager.write_exit_code(name, step['exit_code'])
                break
    
    # Apply progression in background (for testing)
    import threading
    progression_thread = threading.Thread(target=apply_progression, daemon=True)
    progression_thread.start()
    
    return session


# Example usage and testing utilities
if __name__ == "__main__":
    # Example of using the mock screen environment
    print("Screen Mock Utilities - Example Usage")
    
    with create_mock_screen_environment() as mock_screen:
        # Create a few mock sessions
        session1 = mock_screen.create_session("test-session-1", "python script1.py")
        session2 = mock_screen.create_session("test-session-2", "python script2.py")
        
        print(f"Created sessions: {mock_screen.list_sessions()}")
        
        # Send commands
        mock_screen.send_command("test-session-1", "print('Hello from session 1')")
        mock_screen.send_command("test-session-2", "import time; time.sleep(1)")
        
        # Simulate completion
        mock_screen.simulate_completion("test-session-1", exit_code=0)
        mock_screen.simulate_completion("test-session-2", exit_code=1)
        
        # Check session info
        for session_name in mock_screen.list_sessions():
            session = mock_screen.get_session(session_name)
            if session:
                info = session.get_info()
                print(f"Session {session_name}: {info['status']} (exit: {info['exit_code']})")
        
        # Show call history
        print(f"\nCall history: {len(mock_screen.get_call_history())} operations")
        for call in mock_screen.get_call_history()[-3:]:  # Last 3 calls
            print(f"  {call['method']}: {call['args']}")
        
        print("\nMock screen environment demonstrated successfully!")