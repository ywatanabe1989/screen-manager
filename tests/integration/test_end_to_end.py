#!/usr/bin/env python3
"""
Integration tests for end-to-end workflows and multi-agent scenarios.

Tests complete workflows combining cipdb, ScreenSessionManager, MCP server,
and CLI components working together in realistic debugging scenarios.
"""

import os
import time
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

import pytest

from screen_manager.cipdb import get_agent_id, set_trace, check_condition
from screen_manager.screen_manager import ScreenSessionManager
from screen_manager.mcp_server import (
    create_debug_session, get_session_status, wait_for_completion,
    send_command, get_session_output, cleanup_session
)
from screen_manager.cli import main


@pytest.mark.integration
class TestEndToEndWorkflow:
    """Test complete end-to-end debugging workflows."""
    
    @patch('subprocess.run')
    def test_complete_debugging_session(self, mock_subprocess):
        """Test complete debugging session from creation to cleanup."""
        # Setup mock subprocess responses
        def subprocess_side_effect(cmd, *args, **kwargs):
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            
            if 'screen' in cmd and '-dmS' in cmd:
                # Session creation
                result.returncode = 0
            elif 'screen' in cmd and '-ls' in cmd:
                # List sessions - simulate progression from running to completed
                if hasattr(subprocess_side_effect, 'call_count'):
                    subprocess_side_effect.call_count += 1
                else:
                    subprocess_side_effect.call_count = 1
                
                if subprocess_side_effect.call_count <= 2:
                    result.stdout = "There are screens on:\n\t12345.test-agent-debug\t(Detached)\n"
                else:
                    result.stdout = "No Sockets found in /tmp/screens/S-user.\n"
                    result.returncode = 1
            elif 'screen' in cmd and 'stuff' in cmd:
                # Send command
                result.returncode = 0
            
            return result
        
        mock_subprocess.side_effect = subprocess_side_effect
        
        # Step 1: Create session through MCP tool
        with patch('os.path.exists', return_value=False):  # No exit code file initially
            create_result = create_debug_session(
                name="debug",
                command="python -c 'print(\"Hello Debug\"); import time; time.sleep(1); print(\"Done\")'",
                working_dir="/tmp/debug",
                agent_id="test-agent"
            )
        
        assert create_result['success'] is True
        assert create_result['session_name'] == 'test-agent-debug'
        
        # Step 2: Check initial status
        with patch('os.path.exists', return_value=False):
            status_result = get_session_status("debug")
        
        assert status_result['status'] == 'running'
        assert status_result['is_running'] is True
        
        # Step 3: Send debug command
        send_result = send_command("debug", "print('Debug info sent')")
        assert send_result['success'] is True
        
        # Step 4: Simulate session completion with exit code
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="EXIT_CODE:0\n")):
            
            completion_result = wait_for_completion("debug", timeout=5)
        
        assert completion_result['success'] is True
        assert completion_result['status'] == 'completed'
        assert completion_result['exit_code'] == 0
        
        # Step 5: Get output
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="Hello Debug\nDebug info sent\nDone\n")):
            
            output_result = get_session_output("debug", lines=10)
        
        assert "Hello Debug" in output_result['output']
        assert "Done" in output_result['output']
        
        # Step 6: Cleanup
        with patch('os.remove'):  # Mock file removal
            cleanup_result = cleanup_session("debug")
        
        assert cleanup_result['success'] is True
    
    @patch('subprocess.run')
    def test_error_handling_workflow(self, mock_subprocess):
        """Test end-to-end error handling workflow."""
        # Setup subprocess to simulate failures
        def subprocess_side_effect(cmd, *args, **kwargs):
            if 'screen' in cmd and '-dmS' in cmd:
                # Simulate session creation failure
                raise subprocess.CalledProcessError(
                    returncode=1, cmd=cmd, stderr="Screen session creation failed"
                )
            
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            return result
        
        mock_subprocess.side_effect = subprocess_side_effect
        
        # Attempt to create session - should handle failure gracefully
        create_result = create_debug_session(
            name="failing-session",
            command="python broken_script.py",
            agent_id="test-agent"
        )
        
        assert create_result['success'] is False
        assert 'error' in create_result
        
        # Attempt operations on non-existent session
        status_result = get_session_status("nonexistent-session")
        assert status_result['status'] == 'unknown'
        
        send_result = send_command("nonexistent-session", "print('test')")
        assert send_result['success'] is False
    
    def test_session_with_exit_code_handling(self):
        """Test session with proper exit code handling."""
        manager = ScreenSessionManager(agent_id="test-agent")
        
        # Mock session that completes with error
        with patch.object(manager, '_is_screen_session_running') as mock_running, \
             patch('subprocess.run') as mock_subprocess, \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="EXIT_CODE:1\n")) as mock_file:
            
            # Setup mocks
            mock_subprocess.return_value.returncode = 0
            mock_running.return_value = False  # Session completed
            
            # Create session
            create_result = manager.create_session(
                name="error-session",
                command="python -c 'import sys; sys.exit(1)'"
            )
            assert create_result['success'] is True
            
            # Check status - should detect error exit code
            status = manager.get_session_status("error-session")
            assert status['status'] == 'error'
            assert status['exit_code'] == 1
            assert status['is_running'] is False


@pytest.mark.integration
class TestMultiAgentScenarios:
    """Test multi-agent debugging scenarios."""
    
    def test_multiple_agents_separate_sessions(self):
        """Test multiple agents creating separate debugging sessions."""
        agents = ['agent-1', 'agent-2', 'agent-3']
        sessions = {}
        
        # Create sessions for each agent
        for agent_id in agents:
            manager = ScreenSessionManager(agent_id=agent_id)
            
            with patch('subprocess.run') as mock_subprocess:
                mock_subprocess.return_value.returncode = 0
                
                result = manager.create_session(
                    name=f"task-{agent_id}",
                    command=f"python agent_{agent_id}_task.py"
                )
                
                assert result['success'] is True
                expected_session_name = f"{agent_id}-task-{agent_id}"
                assert result['session_name'] == expected_session_name
                sessions[agent_id] = expected_session_name
        
        # Verify sessions are isolated per agent
        assert len(sessions) == 3
        assert all(agent_id in session_name for agent_id, session_name in sessions.items())
    
    def test_conditional_debugging_multi_agent(self, clean_env):
        """Test conditional debugging across multiple agents."""
        agents = ['debug-agent', 'production-agent', 'test-agent']
        debug_calls = []
        
        with patch('screen_manager.cipdb.ipdb') as mock_ipdb:
            mock_ipdb.set_trace = Mock(side_effect=lambda frame: debug_calls.append(get_agent_id()))
            
            for agent_id in agents:
                os.environ['CLAUDE_AGENT_ID'] = agent_id
                
                # Only debug-agent should trigger debugging
                if agent_id == 'debug-agent':
                    set_trace(agent_id='debug-agent')
                else:
                    set_trace(agent_id='debug-agent')  # Should not trigger
            
            # Only debug-agent should have triggered debugging
            assert len(debug_calls) == 1
            assert debug_calls[0] == 'debug-agent'
    
    @patch('subprocess.run')
    def test_agent_coordination_workflow(self, mock_subprocess):
        """Test agents coordinating through MCP tools."""
        # Setup mock subprocess
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = ""
        
        # Agent 1: Creates and starts a session
        agent1_id = "coordinator-agent"
        with patch('screen_manager.mcp_server.get_agent_id', return_value=agent1_id):
            create_result = create_debug_session(
                name="shared-task",
                command="python shared_computation.py",
                agent_id=agent1_id
            )
            
            assert create_result['success'] is True
            session_name = create_result['session_name']
            assert session_name.startswith(agent1_id)
        
        # Agent 2: Monitors the session
        agent2_id = "monitor-agent"
        with patch('screen_manager.mcp_server.get_agent_id', return_value=agent2_id):
            # Monitor can check status of agent1's session
            with patch('os.path.exists', return_value=False):
                status_result = get_session_status(session_name)
            
            assert status_result['session_name'] == session_name
            # Session belongs to agent1 but agent2 can monitor it
            assert agent1_id in session_name
        
        # Agent 3: Sends commands to the session
        agent3_id = "controller-agent"
        with patch('screen_manager.mcp_server.get_agent_id', return_value=agent3_id):
            with patch('screen_manager.screen_manager.ScreenSessionManager._is_screen_session_running', return_value=True):
                send_result = send_command(session_name, "print('Command from agent3')")
            
            assert send_result['success'] is True
    
    def test_agent_priority_debugging(self, clean_env):
        """Test priority-based debugging for different agent types."""
        priority_agents = [
            ('high-priority-agent', True),
            ('medium-priority-agent', False),  
            ('low-priority-agent', False)
        ]
        
        debug_triggered = []
        
        with patch('screen_manager.cipdb.ipdb') as mock_ipdb:
            mock_ipdb.set_trace = Mock(side_effect=lambda frame: debug_triggered.append(get_agent_id()))
            
            for agent_id, should_debug in priority_agents:
                os.environ['CLAUDE_AGENT_ID'] = agent_id
                
                # High priority agent condition
                condition = agent_id.startswith('high-priority')
                set_trace(condition=condition)
        
        # Only high-priority agent should have triggered debugging
        assert len(debug_triggered) == 1
        assert debug_triggered[0] == 'high-priority-agent'


@pytest.mark.integration 
class TestCLIIntegrationWorkflows:
    """Test CLI integration with complete workflows."""
    
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_cli_debug_complete_workflow(self, mock_print, mock_subprocess):
        """Test CLI debug command complete workflow."""
        # Setup subprocess mocking
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = ""
        
        # Simulate session progression
        session_states = ['running', 'running', 'completed']  # Progress over time
        state_index = 0
        
        def mock_get_status(name):
            nonlocal state_index
            current_state = session_states[min(state_index, len(session_states) - 1)]
            state_index += 1
            
            return {
                'session_name': name,
                'status': current_state,
                'exit_code': 0 if current_state == 'completed' else None,
                'is_running': current_state == 'running'
            }
        
        with patch('screen_manager.cli.ScreenSessionManager') as mock_manager_class:
            mock_manager = Mock()
            mock_manager.agent_id = "cli-test-agent"
            mock_manager.create_session.return_value = {
                'success': True,
                'session_name': 'cli-test-agent-workflow',
                'status': 'running'
            }
            mock_manager.get_session_status = mock_get_status
            mock_manager.wait_for_completion.return_value = {
                'success': True,
                'status': 'completed',
                'exit_code': 0,
                'duration': 2.0
            }
            mock_manager.get_output.return_value = "CLI workflow test output\n"
            mock_manager.cleanup_session.return_value = True
            mock_manager_class.return_value = mock_manager
            
            # Test complete CLI workflow
            test_args = [
                'debug',
                '--name', 'workflow',
                '--command', 'python cli_test.py',
                '--create',
                '--wait',
                '--timeout', '30',
                '--cleanup'
            ]
            
            result = main(test_args)
            
            assert result == 0
            mock_manager.create_session.assert_called_once()
            mock_manager.wait_for_completion.assert_called_once()
            mock_manager.get_output.assert_called_once()
            mock_manager.cleanup_session.assert_called_once()
    
    @patch('screen_manager.cli.run_server')
    @patch('screen_manager.cli.get_agent_id')
    @patch('builtins.print')
    def test_cli_serve_integration(self, mock_print, mock_get_agent_id, mock_run_server):
        """Test CLI serve command integration."""
        mock_get_agent_id.return_value = "cli-serve-agent"
        
        # Test serve with different transports
        transport_tests = [
            (['serve'], 'stdio', 'localhost', 8080),
            (['serve', '--transport', 'http'], 'http', 'localhost', 8080),
            (['serve', '--transport', 'sse', '--host', '0.0.0.0', '--port', '9000'], 'sse', '0.0.0.0', 9000)
        ]
        
        for args, expected_transport, expected_host, expected_port in transport_tests:
            mock_run_server.reset_mock()
            
            result = main(args)
            
            assert result == 0
            mock_run_server.assert_called_once_with(expected_transport, expected_host, expected_port)
    
    @patch('subprocess.run')
    @patch('builtins.print')
    def test_cli_info_comprehensive(self, mock_print, mock_subprocess):
        """Test CLI info command comprehensive system check."""
        # Mock screen version check
        version_result = Mock()
        version_result.stdout = "Screen version 4.09.00 (GNU) 30-Jan-22"
        version_result.returncode = 0
        
        # Mock screen session list
        sessions_result = Mock()
        sessions_result.stdout = """There are screens on:
        12345.agent1-debug-session	(Detached)
        12346.agent2-task-session	(Attached)
        12347.cli-test-session	(Detached)
3 Sockets in /tmp/screens/S-user."""
        sessions_result.returncode = 0
        
        mock_subprocess.side_effect = [version_result, sessions_result]
        
        with patch('screen_manager.cli.get_agent_id', return_value="info-test-agent"), \
             patch('os.getcwd', return_value='/test/workspace'), \
             patch.dict(os.environ, {
                 'CLAUDE_AGENT_ID': 'claude-info-test',
                 'AGENT_ID': 'agent-info-test',
                 'DEBUG_ID': 'debug-info-test'
             }):
            
            result = main(['info'])
            
            assert result == 0
            
            # Verify comprehensive info was printed
            print_calls = [call[0][0] for call in mock_print.call_args_list]
            
            # Check key information was displayed
            assert any('Screen Session Manager - System Information' in call for call in print_calls)
            assert any('info-test-agent' in call for call in print_calls)
            assert any('Screen version' in call for call in print_calls)
            assert any('Active screen sessions' in call for call in print_calls)
            assert any('Python:' in call for call in print_calls)
            assert any('Working directory:' in call for call in print_calls)
            assert any('Environment variables:' in call for call in print_calls)


@pytest.mark.integration
class TestRealWorldScenarios:
    """Test realistic debugging scenarios."""
    
    @patch('subprocess.run')
    def test_python_script_debugging_session(self, mock_subprocess):
        """Test debugging a Python script with conditional breakpoints."""
        # Setup realistic subprocess behavior
        def subprocess_behavior(cmd, *args, **kwargs):
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            
            if 'screen' in cmd and '-dmS' in cmd:
                # Session creation succeeds
                pass
            elif 'screen' in cmd and '-ls' in cmd:
                # Session is running initially
                result.stdout = "There are screens on:\n\t12345.debug-agent-python-debug\t(Detached)\n"
            elif 'screen' in cmd and 'hardcopy' in cmd:
                # Output capture
                pass
            
            return result
        
        mock_subprocess.side_effect = subprocess_behavior
        
        # Agent creates debugging session for Python script
        with patch('screen_manager.mcp_server.get_agent_id', return_value='debug-agent'):
            session_result = create_debug_session(
                name="python-debug",
                command="python -c 'import time; print(\"Starting debug\"); time.sleep(0.1); print(\"Debug complete\")'",
                working_dir="/tmp/debug-workspace"
            )
        
        assert session_result['success'] is True
        
        # Check session is running
        with patch('os.path.exists', return_value=False):  # No exit file yet
            status = get_session_status("python-debug")
        
        assert status['status'] == 'running'
        
        # Send conditional debugging command
        with patch('screen_manager.screen_manager.ScreenSessionManager._is_screen_session_running', return_value=True):
            command_result = send_command(
                "python-debug", 
                "import screen_manager.cipdb as cipdb; cipdb.set_trace(condition='CLAUDE_AGENT_ID')"
            )
        
        assert command_result['success'] is True
        
        # Get debug output
        with patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data="Starting debug\n[cipdb] Debug breakpoint hit\nDebug complete\n")):
            
            output = get_session_output("python-debug", lines=20)
        
        assert "Starting debug" in output['output']
        assert "Debug complete" in output['output']
    
    def test_multi_step_debugging_workflow(self):
        """Test multi-step debugging workflow with state management."""
        manager = ScreenSessionManager(agent_id="workflow-agent")
        
        # Track workflow state
        workflow_state = {
            'step': 1,
            'session_created': False,
            'commands_sent': 0,
            'completed': False
        }
        
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value.returncode = 0
            
            # Step 1: Create initial debugging session
            create_result = manager.create_session(
                name="multi-step-debug",
                command="python debug_workflow.py"
            )
            
            assert create_result['success'] is True
            workflow_state['session_created'] = True
            workflow_state['step'] = 2
            
            # Step 2: Send initialization commands
            with patch.object(manager, '_is_screen_session_running', return_value=True):
                init_commands = [
                    "import screen_manager.cipdb as cipdb",
                    "print('Debug session initialized')",
                    "cipdb.set_trace(condition=False)  # Conditional breakpoint setup"
                ]
                
                for cmd in init_commands:
                    send_result = manager.send_command("multi-step-debug", cmd)
                    assert send_result['success'] is True
                    workflow_state['commands_sent'] += 1
                
                workflow_state['step'] = 3
            
            # Step 3: Monitor session progress
            with patch.object(manager, '_is_screen_session_running', return_value=False), \
                 patch.object(manager, '_get_exit_code', return_value=0):
                
                final_status = manager.get_session_status("multi-step-debug")
                
                assert final_status['status'] == 'completed'
                assert final_status['exit_code'] == 0
                workflow_state['completed'] = True
                workflow_state['step'] = 4
        
        # Verify workflow completed successfully
        assert workflow_state['session_created']
        assert workflow_state['commands_sent'] == 3
        assert workflow_state['completed']
        assert workflow_state['step'] == 4
    
    @patch('subprocess.run')
    def test_error_recovery_workflow(self, mock_subprocess):
        """Test error recovery in debugging workflows."""
        # Setup subprocess to simulate intermittent failures
        call_count = 0
        
        def failing_subprocess(cmd, *args, **kwargs):
            nonlocal call_count
            call_count += 1
            
            # First call fails, subsequent calls succeed
            if call_count == 1 and 'screen' in cmd and '-dmS' in cmd:
                raise subprocess.CalledProcessError(
                    returncode=1, cmd=cmd, stderr="Temporary failure"
                )
            
            result = Mock()
            result.returncode = 0
            result.stdout = ""
            return result
        
        mock_subprocess.side_effect = failing_subprocess
        
        # Attempt to create session - first attempt fails
        first_attempt = create_debug_session(
            name="recovery-test",
            command="python recovery_script.py",
            agent_id="recovery-agent"
        )
        
        assert first_attempt['success'] is False
        assert 'error' in first_attempt
        
        # Second attempt succeeds (simulating retry logic)
        second_attempt = create_debug_session(
            name="recovery-test-retry",
            command="python recovery_script.py",
            agent_id="recovery-agent"
        )
        
        assert second_attempt['success'] is True
        assert 'recovery-agent-recovery-test-retry' == second_attempt['session_name']


@pytest.mark.integration
@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance in integrated scenarios."""
    
    @patch('subprocess.run')
    def test_session_management_performance(self, mock_subprocess):
        """Test performance of session management operations."""
        mock_subprocess.return_value.returncode = 0
        mock_subprocess.return_value.stdout = ""
        
        manager = ScreenSessionManager(agent_id="perf-test-agent")
        session_names = [f"perf-session-{i}" for i in range(10)]
        
        # Measure session creation performance
        start_time = time.time()
        
        for session_name in session_names:
            result = manager.create_session(
                name=session_name,
                command=f"python perf_test_{session_name}.py"
            )
            assert result['success'] is True
        
        creation_duration = time.time() - start_time
        
        # Should create 10 sessions in reasonable time
        assert creation_duration < 5.0  # 5 seconds for 10 sessions
        
        # Measure status checking performance
        start_time = time.time()
        
        with patch.object(manager, '_is_screen_session_running', return_value=True), \
             patch.object(manager, '_get_exit_code', return_value=None):
            
            for session_name in session_names:
                status = manager.get_session_status(session_name)
                assert status['status'] == 'running'
        
        status_check_duration = time.time() - start_time
        
        # Should check 10 session statuses quickly
        assert status_check_duration < 1.0  # 1 second for 10 status checks
    
    def test_mcp_tools_response_time(self):
        """Test MCP tools response time performance."""
        # Test multiple rapid MCP tool calls
        operations = [
            (get_session_status, ("test-session",)),
            (send_command, ("test-session", "print('test')")),
            (get_session_output, ("test-session", 10))
        ]
        
        with patch('screen_manager.mcp_server.get_session_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_session_status.return_value = {'status': 'running'}
            mock_manager.send_command.return_value = {'success': True}
            mock_manager.get_output.return_value = "test output"
            mock_manager._is_screen_session_running.return_value = True
            mock_get_manager.return_value = mock_manager
            
            total_start_time = time.time()
            
            for operation, args in operations * 5:  # Run each operation 5 times
                op_start_time = time.time()
                result = operation(*args)
                op_duration = time.time() - op_start_time
                
                # Each operation should be very fast
                assert op_duration < 0.1  # 100ms per operation
            
            total_duration = time.time() - total_start_time
            
            # 15 total operations should complete quickly
            assert total_duration < 2.0  # 2 seconds for 15 operations


if __name__ == "__main__":
    # Import required modules for standalone execution
    import subprocess
    from unittest.mock import mock_open
    
    print("Running integration tests...")
    pytest.main([__file__, "-v", "--tb=short"])