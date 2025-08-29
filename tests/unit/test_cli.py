#!/usr/bin/env python3
"""
Unit tests for CLI interface functionality.

Tests the command-line interface including serve, debug, and info commands,
argument parsing, and integration with the screen session manager.
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

import pytest

from screen_manager.cli import (
    serve_command,
    debug_command,
    info_command,
    main
)


@pytest.mark.unit
class TestServeCommand:
    """Test serve command functionality."""
    
    @patch('screen_manager.cli.run_server')
    @patch('screen_manager.cli.get_agent_id')
    @patch('builtins.print')
    def test_serve_command_stdio(self, mock_print, mock_get_agent_id, mock_run_server):
        """Test serve command with stdio transport."""
        mock_get_agent_id.return_value = "test-agent"
        mock_run_server.return_value = None
        
        # Create mock args
        args = Mock()
        args.transport = "stdio"
        args.host = "localhost"
        args.port = 8080
        
        result = serve_command(args)
        
        assert result == 0
        mock_run_server.assert_called_once_with("stdio", "localhost", 8080)
        mock_print.assert_any_call("Starting Screen Session Manager MCP Server")
        mock_print.assert_any_call(f"Agent ID: test-agent")
        mock_print.assert_any_call("Transport: stdio")
    
    @patch('screen_manager.cli.run_server')
    @patch('screen_manager.cli.get_agent_id')
    @patch('builtins.print')
    def test_serve_command_http(self, mock_print, mock_get_agent_id, mock_run_server):
        """Test serve command with HTTP transport."""
        mock_get_agent_id.return_value = "test-agent"
        
        args = Mock()
        args.transport = "http"
        args.host = "0.0.0.0"
        args.port = 9000
        
        result = serve_command(args)
        
        assert result == 0
        mock_run_server.assert_called_once_with("http", "0.0.0.0", 9000)
        mock_print.assert_any_call("Transport: http")
        mock_print.assert_any_call("Host: 0.0.0.0:9000")
    
    @patch('screen_manager.cli.run_server')
    @patch('screen_manager.cli.get_agent_id')
    def test_serve_command_keyboard_interrupt(self, mock_get_agent_id, mock_run_server):
        """Test serve command handling keyboard interrupt."""
        mock_get_agent_id.return_value = "test-agent"
        mock_run_server.side_effect = KeyboardInterrupt()
        
        args = Mock()
        args.transport = "stdio"
        args.host = "localhost"
        args.port = 8080
        
        with patch('builtins.print') as mock_print:
            result = serve_command(args)
            
            assert result == 0
            mock_print.assert_any_call("\nServer stopped")
    
    @patch('screen_manager.cli.run_server')
    @patch('screen_manager.cli.get_agent_id')
    def test_serve_command_exception(self, mock_get_agent_id, mock_run_server):
        """Test serve command handling general exception."""
        mock_get_agent_id.return_value = "test-agent"
        mock_run_server.side_effect = RuntimeError("Server error")
        
        args = Mock()
        args.transport = "stdio"
        args.host = "localhost"
        args.port = 8080
        
        with patch('builtins.print') as mock_print:
            result = serve_command(args)
            
            assert result == 1
            mock_print.assert_any_call("Error: Server error")


@pytest.mark.unit
class TestDebugCommand:
    """Test debug command functionality."""
    
    @patch('screen_manager.cli.ScreenSessionManager')
    @patch('builtins.print')
    def test_debug_command_create_session(self, mock_print, mock_manager_class):
        """Test debug command creating new session."""
        # Setup mock manager
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_manager.create_session.return_value = {
            'success': True,
            'session_name': 'test-agent-debug',
            'status': 'running',
            'message': 'Session created successfully'
        }
        mock_manager_class.return_value = mock_manager
        
        # Setup args
        args = Mock()
        args.create = True
        args.name = "debug"
        args.command = "python test.py"
        args.working_dir = "/tmp/test"
        args.wait = False
        args.cleanup = False
        
        result = debug_command(args)
        
        assert result == 0
        mock_manager.create_session.assert_called_once_with("debug", "python test.py", "/tmp/test")
        mock_print.assert_any_call("Agent ID: test-agent")
    
    @patch('screen_manager.cli.ScreenSessionManager')
    @patch('builtins.print')
    def test_debug_command_create_and_wait(self, mock_print, mock_manager_class):
        """Test debug command creating session and waiting for completion."""
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_manager.create_session.return_value = {
            'success': True,
            'session_name': 'test-agent-debug',
            'status': 'running'
        }
        mock_manager.wait_for_completion.return_value = {
            'success': True,
            'status': 'completed',
            'exit_code': 0
        }
        mock_manager.get_output.return_value = "Test output\n"
        mock_manager_class.return_value = mock_manager
        
        args = Mock()
        args.create = True
        args.name = "debug"
        args.command = "python test.py"
        args.working_dir = None
        args.wait = True
        args.timeout = 30
        args.cleanup = True
        
        result = debug_command(args)
        
        assert result == 0
        mock_manager.create_session.assert_called_once()
        mock_manager.wait_for_completion.assert_called_once_with("debug", 30)
        mock_manager.get_output.assert_called_once_with("debug")
        mock_manager.cleanup_session.assert_called_once_with("debug")
    
    @patch('screen_manager.cli.ScreenSessionManager')
    @patch('builtins.print')
    def test_debug_command_get_status(self, mock_print, mock_manager_class):
        """Test debug command getting session status."""
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_manager.get_session_status.return_value = {
            'session_name': 'test-agent-debug',
            'status': 'running',
            'exit_code': None,
            'is_running': True
        }
        mock_manager_class.return_value = mock_manager
        
        args = Mock()
        args.create = False
        args.status = True
        args.name = "debug"
        args.list = False
        args.output = False
        args.cleanup = False
        
        result = debug_command(args)
        
        assert result == 0
        mock_manager.get_session_status.assert_called_once_with("debug")
    
    @patch('screen_manager.cli.ScreenSessionManager')
    @patch('builtins.print')
    def test_debug_command_list_sessions(self, mock_print, mock_manager_class):
        """Test debug command listing all sessions."""
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_manager.list_sessions.return_value = [
            {'session_name': 'test-agent-session1', 'status': 'running', 'exit_code': None},
            {'session_name': 'test-agent-session2', 'status': 'completed', 'exit_code': 0}
        ]
        mock_manager_class.return_value = mock_manager
        
        args = Mock()
        args.create = False
        args.status = False
        args.list = True
        args.output = False
        args.cleanup = False
        
        result = debug_command(args)
        
        assert result == 0
        mock_manager.list_sessions.assert_called_once()
        mock_print.assert_any_call("Active sessions (2):")
    
    @patch('screen_manager.cli.ScreenSessionManager')
    @patch('builtins.print')
    def test_debug_command_get_output(self, mock_print, mock_manager_class):
        """Test debug command getting session output."""
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_manager.get_output.return_value = "Session output line 1\nSession output line 2\n"
        mock_manager_class.return_value = mock_manager
        
        args = Mock()
        args.create = False
        args.status = False
        args.list = False
        args.output = True
        args.name = "debug"
        args.lines = 10
        args.cleanup = False
        
        result = debug_command(args)
        
        assert result == 0
        mock_manager.get_output.assert_called_once_with("debug", 10)
        mock_print.assert_any_call("Session output (10 lines):")
    
    @patch('screen_manager.cli.ScreenSessionManager')
    @patch('builtins.print')
    def test_debug_command_cleanup(self, mock_print, mock_manager_class):
        """Test debug command cleaning up session."""
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_manager.cleanup_session.return_value = True
        mock_manager_class.return_value = mock_manager
        
        args = Mock()
        args.create = False
        args.status = False
        args.list = False
        args.output = False
        args.name = "debug"
        args.cleanup = True
        
        result = debug_command(args)
        
        assert result == 0
        mock_manager.cleanup_session.assert_called_once_with("debug")
        mock_print.assert_any_call("Cleanup successful")
    
    @patch('screen_manager.cli.ScreenSessionManager')
    @patch('builtins.print')
    def test_debug_command_no_action(self, mock_print, mock_manager_class):
        """Test debug command with no action specified."""
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_manager_class.return_value = mock_manager
        
        args = Mock()
        args.create = False
        args.status = False
        args.list = False
        args.output = False
        args.cleanup = False
        
        result = debug_command(args)
        
        assert result == 1
        mock_print.assert_any_call("No action specified. Use --create, --status, --list, --output, or --cleanup")


@pytest.mark.unit
class TestInfoCommand:
    """Test info command functionality."""
    
    @patch('screen_manager.cli.get_agent_id')
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_info_command_success(self, mock_print, mock_subprocess, mock_get_agent_id):
        """Test successful info command execution."""
        mock_get_agent_id.return_value = "test-agent-123"
        
        # Mock screen --version
        version_result = Mock()
        version_result.stdout = "Screen version 4.09.00 (GNU) 30-Jan-22"
        version_result.returncode = 0
        
        # Mock screen -ls  
        ls_result = Mock()
        ls_result.stdout = "There are screens on:\n\t12345.test-session\t(Detached)\n"
        ls_result.returncode = 0
        
        mock_subprocess.side_effect = [version_result, ls_result]
        
        with patch('os.getcwd', return_value='/test/directory'), \
             patch.dict(os.environ, {'CLAUDE_AGENT_ID': 'claude-test', 'DEBUG_ID': 'debug-test'}):
            
            result = info_command(Mock())
            
            assert result == 0
            mock_print.assert_any_call("Screen Session Manager - System Information")
            mock_print.assert_any_call("Agent ID: test-agent-123")
            mock_print.assert_any_call("Screen version: Screen version 4.09.00 (GNU) 30-Jan-22")
            mock_print.assert_any_call("Active screen sessions:")
    
    @patch('screen_manager.cli.get_agent_id')
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_info_command_screen_not_found(self, mock_print, mock_subprocess, mock_get_agent_id):
        """Test info command when screen is not installed."""
        mock_get_agent_id.return_value = "test-agent"
        mock_subprocess.side_effect = FileNotFoundError("screen not found")
        
        result = info_command(Mock())
        
        assert result == 1
        mock_print.assert_any_call("ERROR: screen command not found. Please install screen.")
    
    @patch('screen_manager.cli.get_agent_id')
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_info_command_no_sessions(self, mock_print, mock_subprocess, mock_get_agent_id):
        """Test info command with no active sessions."""
        mock_get_agent_id.return_value = "test-agent"
        
        # Mock screen --version (success)
        version_result = Mock()
        version_result.stdout = "Screen version 4.09.00"
        
        # Mock screen -ls (no sessions)
        ls_result = Mock()
        ls_result.returncode = 1  # Non-zero return code when no sessions
        
        mock_subprocess.side_effect = [version_result, ls_result]
        
        result = info_command(Mock())
        
        assert result == 0
        mock_print.assert_any_call("No active screen sessions")
    
    @patch('screen_manager.cli.get_agent_id')
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_info_command_environment_variables(self, mock_print, mock_subprocess, mock_get_agent_id):
        """Test info command displays environment variables correctly."""
        mock_get_agent_id.return_value = "test-agent"
        
        # Mock subprocess calls
        version_result = Mock()
        version_result.stdout = "Screen version 4.09.00"
        
        ls_result = Mock()
        ls_result.returncode = 1
        
        mock_subprocess.side_effect = [version_result, ls_result]
        
        # Test with various environment variable combinations
        test_env = {
            'CLAUDE_AGENT_ID': 'claude-123',
            'AGENT_ID': 'agent-456',
            # DEBUG_ID intentionally not set
        }
        
        with patch.dict(os.environ, test_env, clear=False):
            result = info_command(Mock())
            
            assert result == 0
            mock_print.assert_any_call("Environment variables:")
            # Should show set and unset variables
            call_args = [call[0][0] for call in mock_print.call_args_list if 'CLAUDE_AGENT_ID' in call[0][0]]
            assert any('claude-123' in arg for arg in call_args)


@pytest.mark.unit
class TestMainFunction:
    """Test main CLI function and argument parsing."""
    
    def test_main_no_command(self):
        """Test main function with no command specified."""
        with patch('sys.argv', ['cli.py']), \
             patch('builtins.print') as mock_print:
            
            result = main()
            
            assert result == 1
            # Should print help
            assert mock_print.called
    
    @patch('screen_manager.cli.serve_command')
    def test_main_serve_command(self, mock_serve_command):
        """Test main function with serve command."""
        mock_serve_command.return_value = 0
        
        test_args = [
            'cli.py', 'serve',
            '--transport', 'http',
            '--host', '0.0.0.0',
            '--port', '9000'
        ]
        
        with patch('sys.argv', test_args):
            result = main()
            
            assert result == 0
            mock_serve_command.assert_called_once()
            
            # Check that args were parsed correctly
            args = mock_serve_command.call_args[0][0]
            assert args.transport == 'http'
            assert args.host == '0.0.0.0'
            assert args.port == 9000
    
    @patch('screen_manager.cli.debug_command')
    def test_main_debug_command(self, mock_debug_command):
        """Test main function with debug command."""
        mock_debug_command.return_value = 0
        
        test_args = [
            'cli.py', 'debug',
            '--name', 'test-session',
            '--command', 'python script.py',
            '--create',
            '--wait',
            '--timeout', '60',
            '--cleanup'
        ]
        
        with patch('sys.argv', test_args):
            result = main()
            
            assert result == 0
            mock_debug_command.assert_called_once()
            
            # Check that args were parsed correctly
            args = mock_debug_command.call_args[0][0]
            assert args.name == 'test-session'
            assert args.command == 'python script.py'
            assert args.create is True
            assert args.wait is True
            assert args.timeout == 60
            assert args.cleanup is True
    
    @patch('screen_manager.cli.info_command')
    def test_main_info_command(self, mock_info_command):
        """Test main function with info command."""
        mock_info_command.return_value = 0
        
        test_args = ['cli.py', 'info']
        
        with patch('sys.argv', test_args):
            result = main()
            
            assert result == 0
            mock_info_command.assert_called_once()
    
    def test_main_with_custom_args(self):
        """Test main function with custom argument list."""
        test_args = ['serve', '--transport', 'sse', '--port', '8888']
        
        with patch('screen_manager.cli.serve_command', return_value=0) as mock_serve:
            result = main(test_args)
            
            assert result == 0
            mock_serve.assert_called_once()
            
            args = mock_serve.call_args[0][0]
            assert args.transport == 'sse'
            assert args.port == 8888


@pytest.mark.unit
class TestArgumentParsing:
    """Test argument parsing for different commands."""
    
    def test_serve_parser_defaults(self):
        """Test serve command parser with default values."""
        from screen_manager.cli import main
        
        with patch('screen_manager.cli.serve_command', return_value=0) as mock_serve:
            main(['serve'])
            
            args = mock_serve.call_args[0][0]
            assert args.transport == 'stdio'
            assert args.host == 'localhost'
            assert args.port == 8080
    
    def test_debug_parser_defaults(self):
        """Test debug command parser with default values."""
        from screen_manager.cli import main
        
        with patch('screen_manager.cli.debug_command', return_value=0) as mock_debug:
            main(['debug'])
            
            args = mock_debug.call_args[0][0]
            assert args.name == 'debug-session'
            assert args.lines == 20
            assert args.timeout == 30
            assert args.create is False
            assert args.wait is False
            assert args.cleanup is False
    
    def test_debug_parser_all_options(self):
        """Test debug command parser with all options."""
        from screen_manager.cli import main
        
        test_args = [
            'debug',
            '--name', 'custom-session',
            '--command', 'python custom.py',
            '--working-dir', '/custom/path',
            '--create',
            '--status',
            '--list',
            '--output',
            '--lines', '50',
            '--wait',
            '--timeout', '120',
            '--cleanup'
        ]
        
        with patch('screen_manager.cli.debug_command', return_value=0) as mock_debug:
            main(test_args)
            
            args = mock_debug.call_args[0][0]
            assert args.name == 'custom-session'
            assert args.command == 'python custom.py'
            assert args.working_dir == '/custom/path'
            assert args.create is True
            assert args.status is True
            assert args.list is True
            assert args.output is True
            assert args.lines == 50
            assert args.wait is True
            assert args.timeout == 120
            assert args.cleanup is True


@pytest.mark.integration
class TestCLIIntegration:
    """Integration tests for CLI functionality."""
    
    @patch('screen_manager.cli.run_server')
    @patch('screen_manager.cli.get_agent_id')
    def test_cli_serve_integration(self, mock_get_agent_id, mock_run_server):
        """Test CLI serve command integration."""
        mock_get_agent_id.return_value = "integration-test-agent"
        
        # Test that serve command properly integrates with MCP server
        test_args = ['serve', '--transport', 'stdio']
        
        with patch('builtins.print'):
            result = main(test_args)
            
            assert result == 0
            mock_run_server.assert_called_once_with('stdio', 'localhost', 8080)
    
    @patch('screen_manager.cli.ScreenSessionManager')
    def test_cli_debug_full_workflow(self, mock_manager_class):
        """Test CLI debug command full workflow."""
        # Setup comprehensive mock manager
        mock_manager = Mock()
        mock_manager.agent_id = "cli-integration-agent"
        mock_manager.create_session.return_value = {
            'success': True,
            'session_name': 'cli-integration-agent-workflow',
            'status': 'running'
        }
        mock_manager.wait_for_completion.return_value = {
            'success': True,
            'status': 'completed',
            'exit_code': 0,
            'duration': 1.5
        }
        mock_manager.get_output.return_value = "Integration test output\nCompleted successfully\n"
        mock_manager.cleanup_session.return_value = True
        mock_manager_class.return_value = mock_manager
        
        # Test full workflow: create -> wait -> output -> cleanup
        test_args = [
            'debug',
            '--name', 'integration-workflow',
            '--command', 'python integration_test.py',
            '--create',
            '--wait',
            '--cleanup'
        ]
        
        with patch('builtins.print'):
            result = main(test_args)
            
            assert result == 0
            mock_manager.create_session.assert_called_once()
            mock_manager.wait_for_completion.assert_called_once()
            mock_manager.get_output.assert_called_once()
            mock_manager.cleanup_session.assert_called_once()


@pytest.mark.unit
@pytest.mark.performance
class TestCLIPerformance:
    """Test CLI performance requirements."""
    
    def test_argument_parsing_performance(self):
        """Test that argument parsing is fast."""
        import time
        
        test_args = [
            'debug',
            '--name', 'performance-test',
            '--command', 'python script.py',
            '--create',
            '--wait',
            '--timeout', '60'
        ]
        
        start_time = time.time()
        
        with patch('screen_manager.cli.debug_command', return_value=0):
            main(test_args)
            
        duration = time.time() - start_time
        
        # Argument parsing should be very fast
        assert duration < 0.1  # 100ms
    
    @patch('screen_manager.cli.get_agent_id')
    def test_info_command_performance(self, mock_get_agent_id):
        """Test info command performance."""
        import time
        
        mock_get_agent_id.return_value = "perf-test-agent"
        
        # Mock fast subprocess calls
        fast_result = Mock()
        fast_result.stdout = "Quick result"
        fast_result.returncode = 0
        
        with patch('subprocess.run', return_value=fast_result), \
             patch('builtins.print'), \
             patch('os.getcwd', return_value='/test'):
            
            start_time = time.time()
            info_command(Mock())
            duration = time.time() - start_time
            
            # Info command should be reasonably fast
            assert duration < 1.0  # 1 second


if __name__ == "__main__":
    print("Running CLI unit tests...")
    pytest.main([__file__, "-v"])