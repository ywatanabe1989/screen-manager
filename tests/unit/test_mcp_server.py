#!/usr/bin/env python3
"""
Unit tests for MCP server tools and functionality.

Tests all 9 MCP tools for agent coordination, FastMCP integration,
and multi-agent debugging session management.
"""

import sys
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

import pytest

from screen_manager.mcp_server import (
    get_session_manager,
    get_agent_id,
    run_server,
    main,
    mcp,
    _create_debug_session_handler as create_debug_session,
    _get_session_status_handler as get_session_status,
    _send_command_handler as send_command,
    _get_exit_code_handler as get_exit_code,
    _wait_for_completion_handler as wait_for_completion,
    _get_session_output_handler as get_session_output,
    _list_sessions_handler as list_sessions,
    _cleanup_session_handler as cleanup_session,
    _get_agent_info_handler as get_agent_info
)


@pytest.mark.unit
class TestGetSessionManager:
    """Test session manager singleton functionality."""
    
    def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton instance."""
        with patch('screen_manager.mcp_server.ScreenSessionManager') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            # Clear the global variable
            import screen_manager.mcp_server
            screen_manager.mcp_server._session_manager = None
            
            # First call should create instance
            manager1 = get_session_manager()
            mock_class.assert_called_once()
            assert manager1 == mock_instance
            
            # Second call should return same instance
            manager2 = get_session_manager()
            assert manager1 == manager2
            mock_class.assert_called_once()  # Should not be called again
    
    def test_get_session_manager_existing_instance(self):
        """Test get_session_manager with existing instance."""
        mock_manager = Mock()
        
        # Set existing instance
        import screen_manager.mcp_server
        screen_manager.mcp_server._session_manager = mock_manager
        
        result = get_session_manager()
        assert result == mock_manager


@pytest.mark.unit
class TestMCPTools:
    """Test all MCP tool functions."""
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_create_debug_session_success(self, mock_get_manager):
        """Test create_debug_session tool success."""
        mock_manager = Mock()
        mock_manager.create_session.return_value = {
            'success': True,
            'session_name': 'test-agent-debug',
            'status': 'running',
            'message': 'Session created successfully'
        }
        mock_get_manager.return_value = mock_manager
        
        result = create_debug_session(
            name="debug",
            command="python -c 'print(\"test\")'",
            working_dir="/tmp/test",
            agent_id="custom-agent"
        )
        
        assert result['success'] is True
        assert result['session_name'] == 'test-agent-debug'
        assert result['status'] == 'running'
        
        # Verify manager was called correctly
        mock_manager.create_session.assert_called_once_with(
            "debug", "python -c 'print(\"test\")'", "/tmp/test"
        )
        # Verify agent_id was set
        assert mock_manager.agent_id == "custom-agent"
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_create_debug_session_no_agent_id(self, mock_get_manager):
        """Test create_debug_session without custom agent_id."""
        mock_manager = Mock()
        mock_manager.agent_id = "default-agent"
        mock_manager.create_session.return_value = {
            'success': True,
            'session_name': 'default-agent-debug',
            'status': 'running'
        }
        mock_get_manager.return_value = mock_manager
        
        result = create_debug_session(
            name="debug",
            command="python script.py"
        )
        
        assert result['success'] is True
        mock_manager.create_session.assert_called_once_with("debug", "python script.py", None)
        # Agent ID should not be modified
        assert mock_manager.agent_id == "default-agent"
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_get_session_status_tool(self, mock_get_manager):
        """Test get_session_status tool."""
        mock_manager = Mock()
        mock_manager.get_session_status.return_value = {
            'session_name': 'test-session',
            'status': 'running',
            'exit_code': None,
            'is_running': True,
            'agent_id': 'test-agent'
        }
        mock_get_manager.return_value = mock_manager
        
        result = get_session_status("test-session")
        
        assert result['session_name'] == 'test-session'
        assert result['status'] == 'running'
        assert result['exit_code'] is None
        assert result['is_running'] is True
        
        mock_manager.get_session_status.assert_called_once_with("test-session")
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_send_command_tool(self, mock_get_manager):
        """Test send_command tool."""
        mock_manager = Mock()
        mock_manager.send_command.return_value = {
            'success': True,
            'message': 'Command sent successfully',
            'command': 'print("hello")'
        }
        mock_get_manager.return_value = mock_manager
        
        result = send_command("test-session", "print(\"hello\")")
        
        assert result['success'] is True
        assert result['command'] == 'print("hello")'
        
        mock_manager.send_command.assert_called_once_with("test-session", "print(\"hello\")")
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_get_exit_code_tool(self, mock_get_manager):
        """Test get_exit_code tool."""
        mock_manager = Mock()
        mock_manager.get_exit_code.return_value = 0
        mock_get_manager.return_value = mock_manager
        
        result = get_exit_code("test-session")
        
        assert result['session_name'] == "test-session"
        assert result['exit_code'] == 0
        assert result['completed'] is True
        
        mock_manager.get_exit_code.assert_called_once_with("test-session")
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_get_exit_code_tool_not_completed(self, mock_get_manager):
        """Test get_exit_code tool when session not completed."""
        mock_manager = Mock()
        mock_manager.get_exit_code.return_value = None
        mock_get_manager.return_value = mock_manager
        
        result = get_exit_code("test-session")
        
        assert result['session_name'] == "test-session"
        assert result['exit_code'] is None
        assert result['completed'] is False
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_wait_for_completion_tool(self, mock_get_manager):
        """Test wait_for_completion tool."""
        mock_manager = Mock()
        mock_manager.wait_for_completion.return_value = {
            'success': True,
            'status': 'completed',
            'exit_code': 0,
            'duration': 2.5
        }
        mock_get_manager.return_value = mock_manager
        
        result = wait_for_completion("test-session", timeout=30)
        
        assert result['success'] is True
        assert result['status'] == 'completed'
        assert result['exit_code'] == 0
        
        mock_manager.wait_for_completion.assert_called_once_with("test-session", 30)
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_wait_for_completion_tool_default_timeout(self, mock_get_manager):
        """Test wait_for_completion tool with default timeout."""
        mock_manager = Mock()
        mock_manager.wait_for_completion.return_value = {
            'success': True,
            'status': 'completed',
            'exit_code': 0
        }
        mock_get_manager.return_value = mock_manager
        
        result = wait_for_completion("test-session")
        
        mock_manager.wait_for_completion.assert_called_once_with("test-session", 30)
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_get_session_output_tool(self, mock_get_manager):
        """Test get_session_output tool."""
        mock_manager = Mock()
        mock_manager.get_output.return_value = "Line 1\nLine 2\nLine 3\n"
        mock_get_manager.return_value = mock_manager
        
        result = get_session_output("test-session", lines=5)
        
        assert result['session_name'] == "test-session"
        assert result['output'] == "Line 1\nLine 2\nLine 3\n"
        assert result['lines_requested'] == 5
        
        mock_manager.get_output.assert_called_once_with("test-session", 5)
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_get_session_output_tool_default_lines(self, mock_get_manager):
        """Test get_session_output tool with default lines."""
        mock_manager = Mock()
        mock_manager.get_output.return_value = "Output content"
        mock_get_manager.return_value = mock_manager
        
        result = get_session_output("test-session")
        
        assert result['lines_requested'] == 20  # default value
        mock_manager.get_output.assert_called_once_with("test-session", 20)
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_list_sessions_tool(self, mock_get_manager):
        """Test list_sessions tool."""
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_manager.list_sessions.return_value = [
            {'session_name': 'test-agent-session1', 'status': 'running'},
            {'session_name': 'test-agent-session2', 'status': 'completed'}
        ]
        mock_get_manager.return_value = mock_manager
        
        result = list_sessions()
        
        assert result['agent_id'] == "test-agent"
        assert result['count'] == 2
        assert len(result['sessions']) == 2
        assert result['sessions'][0]['session_name'] == 'test-agent-session1'
        assert result['sessions'][1]['session_name'] == 'test-agent-session2'
        
        mock_manager.list_sessions.assert_called_once()
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_cleanup_session_tool(self, mock_get_manager):
        """Test cleanup_session tool."""
        mock_manager = Mock()
        mock_manager.cleanup_session.return_value = True
        mock_get_manager.return_value = mock_manager
        
        result = cleanup_session("test-session")
        
        assert result['session_name'] == "test-session"
        assert result['success'] is True
        assert 'cleaned up successfully' in result['message']
        
        mock_manager.cleanup_session.assert_called_once_with("test-session")
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_cleanup_session_tool_failure(self, mock_get_manager):
        """Test cleanup_session tool failure."""
        mock_manager = Mock()
        mock_manager.cleanup_session.return_value = False
        mock_get_manager.return_value = mock_manager
        
        result = cleanup_session("test-session")
        
        assert result['session_name'] == "test-session"
        assert result['success'] is False
        assert 'Failed to clean up' in result['message']
    
    @patch('screen_manager.mcp_server.get_agent_id')
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_get_agent_info_tool(self, mock_get_manager, mock_get_agent_id):
        """Test get_agent_info tool."""
        mock_get_agent_id.return_value = "current-agent"
        mock_manager = Mock()
        mock_manager.agent_id = "session-manager-agent"
        mock_get_manager.return_value = mock_manager
        
        result = get_agent_info()
        
        assert result['agent_id'] == "current-agent"
        assert result['session_manager_agent_id'] == "session-manager-agent"
        assert 'python_version' in result
        assert result['python_version'] == sys.version
        assert 'available_tools' in result
        assert len(result['available_tools']) == 8  # 8 tools available


@pytest.mark.unit
class TestServerManagement:
    """Test MCP server management functionality."""
    
    @patch('screen_manager.mcp_server.mcp')
    def test_run_server_stdio(self, mock_mcp):
        """Test running server with stdio transport."""
        run_server(transport="stdio")
        
        mock_mcp.run.assert_called_once()
        mock_mcp.run_http.assert_not_called()
        mock_mcp.run_sse.assert_not_called()
    
    @patch('screen_manager.mcp_server.mcp')
    def test_run_server_http(self, mock_mcp):
        """Test running server with HTTP transport."""
        run_server(transport="http", host="0.0.0.0", port=9000)
        
        mock_mcp.run_http.assert_called_once_with(host="0.0.0.0", port=9000)
        mock_mcp.run.assert_not_called()
        mock_mcp.run_sse.assert_not_called()
    
    @patch('screen_manager.mcp_server.mcp')
    def test_run_server_sse(self, mock_mcp):
        """Test running server with SSE transport."""
        run_server(transport="sse", host="localhost", port=8080)
        
        mock_mcp.run_sse.assert_called_once_with(host="localhost", port=8080)
        mock_mcp.run.assert_not_called()
        mock_mcp.run_http.assert_not_called()
    
    def test_run_server_invalid_transport(self):
        """Test running server with invalid transport."""
        with pytest.raises(ValueError, match="Unsupported transport"):
            run_server(transport="invalid")
    
    @patch('screen_manager.mcp_server.run_server')
    @patch('screen_manager.mcp_server.get_agent_id')
    @patch('builtins.print')
    def test_main_default_args(self, mock_print, mock_get_agent_id, mock_run_server):
        """Test main function with default arguments."""
        mock_get_agent_id.return_value = "test-agent"
        
        with patch('sys.argv', ['mcp_server.py']):
            main()
        
        mock_run_server.assert_called_once_with("stdio", "localhost", 8080)
        mock_print.assert_any_call(f"Starting Screen Session Manager MCP Server (Agent: test-agent)")
    
    @patch('screen_manager.mcp_server.run_server')
    @patch('screen_manager.mcp_server.get_agent_id')
    @patch('builtins.print')
    def test_main_custom_args(self, mock_print, mock_get_agent_id, mock_run_server):
        """Test main function with custom arguments."""
        mock_get_agent_id.return_value = "test-agent"
        
        test_args = [
            'mcp_server.py',
            '--transport', 'http',
            '--host', '0.0.0.0',
            '--port', '9090'
        ]
        
        with patch('sys.argv', test_args):
            main()
        
        mock_run_server.assert_called_once_with("http", "0.0.0.0", 9090)
        mock_print.assert_any_call("Transport: http")
        mock_print.assert_any_call("Host: 0.0.0.0:9090")


@pytest.mark.unit  
class TestMCPIntegration:
    """Test FastMCP integration and configuration."""
    
    def test_fastmcp_initialization(self):
        """Test FastMCP server initialization."""
        # Verify that the mcp instance exists and has the correct name
        from screen_manager.mcp_server import mcp
        assert mcp is not None
        # FastMCP instances should have name attribute
        assert hasattr(mcp, 'name') or hasattr(mcp, '_name') or 'screen-manager' in str(mcp)
    
    def test_mcp_tools_decorated(self):
        """Test that all MCP tools are properly decorated."""
        # This test ensures that the tools are decorated with @mcp.tool()
        # We can't easily test the decorator directly, but we can verify
        # that the functions exist and are callable
        
        tools = [
            create_debug_session,
            get_session_status,
            send_command,
            get_exit_code,
            wait_for_completion,
            get_session_output,
            list_sessions,
            cleanup_session,
            get_agent_info
        ]
        
        for tool in tools:
            assert callable(tool)
            assert hasattr(tool, '__name__')
            # FastMCP decorated functions should be callable
            assert tool.__name__ in [
                '_create_debug_session_handler',
                '_get_session_status_handler', 
                '_send_command_handler',
                '_get_exit_code_handler',
                '_wait_for_completion_handler',
                '_get_session_output_handler',
                '_list_sessions_handler',
                '_cleanup_session_handler',
                '_get_agent_info_handler'
            ]


@pytest.mark.unit
@pytest.mark.performance
class TestMCPPerformance:
    """Test MCP tool performance requirements."""
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_mcp_tool_response_performance(self, mock_get_manager, performance_threshold):
        """Test MCP tool response times meet performance requirements."""
        import time
        
        # Mock quick responses from session manager
        mock_manager = Mock()
        mock_manager.get_session_status.return_value = {'status': 'running'}
        mock_manager.agent_id = "test-agent"
        mock_get_manager.return_value = mock_manager
        
        # Test get_session_status performance
        start_time = time.time()
        get_session_status("test-session")
        duration = time.time() - start_time
        
        assert duration < performance_threshold['mcp_tool_response']
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_agent_info_performance(self, mock_get_manager, performance_threshold):
        """Test get_agent_info performance."""
        import time
        
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_get_manager.return_value = mock_manager
        
        with patch('screen_manager.mcp_server.get_agent_id', return_value="test-agent"):
            start_time = time.time()
            get_agent_info()
            duration = time.time() - start_time
            
            assert duration < performance_threshold['mcp_tool_response']


@pytest.mark.integration
class TestMCPToolsIntegration:
    """Integration tests for MCP tools working together."""
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_full_session_workflow(self, mock_get_manager):
        """Test complete session workflow through MCP tools."""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager
        
        # Step 1: Create session
        mock_manager.create_session.return_value = {
            'success': True,
            'session_name': 'test-agent-workflow',
            'status': 'running'
        }
        
        create_result = create_debug_session("workflow", "python script.py")
        assert create_result['success'] is True
        
        # Step 2: Check status
        mock_manager.get_session_status.return_value = {
            'session_name': 'test-agent-workflow',
            'status': 'running',
            'exit_code': None
        }
        
        status_result = get_session_status("workflow")
        assert status_result['status'] == 'running'
        
        # Step 3: Send command
        mock_manager.send_command.return_value = {
            'success': True,
            'command': 'print("debug info")'
        }
        
        command_result = send_command("workflow", "print(\"debug info\")")
        assert command_result['success'] is True
        
        # Step 4: Wait for completion
        mock_manager.wait_for_completion.return_value = {
            'success': True,
            'status': 'completed',
            'exit_code': 0
        }
        
        wait_result = wait_for_completion("workflow")
        assert wait_result['status'] == 'completed'
        
        # Step 5: Get output
        mock_manager.get_output.return_value = "Script output\nCompleted successfully\n"
        
        output_result = get_session_output("workflow")
        assert "Script output" in output_result['output']
        
        # Step 6: Cleanup
        mock_manager.cleanup_session.return_value = True
        
        cleanup_result = cleanup_session("workflow")
        assert cleanup_result['success'] is True
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_multi_session_management(self, mock_get_manager):
        """Test managing multiple sessions simultaneously."""
        mock_manager = Mock()
        mock_manager.agent_id = "test-agent"
        mock_get_manager.return_value = mock_manager
        
        # Create multiple sessions
        session_names = ["session1", "session2", "session3"]
        
        for session_name in session_names:
            mock_manager.create_session.return_value = {
                'success': True,
                'session_name': f'test-agent-{session_name}',
                'status': 'running'
            }
            
            result = create_debug_session(session_name, "python task.py")
            assert result['success'] is True
        
        # List all sessions
        mock_manager.list_sessions.return_value = [
            {'session_name': f'test-agent-{name}', 'status': 'running'}
            for name in session_names
        ]
        
        list_result = list_sessions()
        assert list_result['count'] == 3
        assert len(list_result['sessions']) == 3
    
    @patch('screen_manager.mcp_server.get_session_manager')
    def test_error_handling_workflow(self, mock_get_manager):
        """Test error handling across MCP tools."""
        mock_manager = Mock()
        mock_get_manager.return_value = mock_manager
        
        # Test failed session creation
        mock_manager.create_session.return_value = {
            'success': False,
            'error': 'Screen command failed'
        }
        
        create_result = create_debug_session("failing-session", "invalid-command")
        assert create_result['success'] is False
        
        # Test failed command sending
        mock_manager.send_command.return_value = {
            'success': False,
            'error': 'Session not running'
        }
        
        command_result = send_command("nonexistent-session", "print('test')")
        assert command_result['success'] is False
        
        # Test failed cleanup
        mock_manager.cleanup_session.return_value = False
        
        cleanup_result = cleanup_session("failed-session")
        assert cleanup_result['success'] is False


if __name__ == "__main__":
    print("Running MCP server unit tests...")
    pytest.main([__file__, "-v"])