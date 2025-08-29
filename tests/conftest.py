#!/usr/bin/env python3
"""
Test configuration and fixtures for screen-manager test suite.

Provides common fixtures, mocks, and utilities for testing multi-agent
debugging functionality with screen sessions.
"""

import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Generator, Optional

import pytest


@pytest.fixture
def temp_agent_id() -> str:
    """Generate a unique agent ID for testing."""
    return f"test-agent-{uuid.uuid4().hex[:8]}"


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Clean environment variables for isolated testing."""
    original_env = os.environ.copy()
    
    # Clear agent-related environment variables
    agent_vars = ['CLAUDE_AGENT_ID', 'AGENT_ID', 'DEBUG_ID']
    for var in agent_vars:
        if var in os.environ:
            del os.environ[var]
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture
def set_agent_env(temp_agent_id: str) -> Generator[str, None, None]:
    """Set CLAUDE_AGENT_ID environment variable."""
    original = os.environ.get('CLAUDE_AGENT_ID')
    os.environ['CLAUDE_AGENT_ID'] = temp_agent_id
    
    yield temp_agent_id
    
    if original is not None:
        os.environ['CLAUDE_AGENT_ID'] = original
    elif 'CLAUDE_AGENT_ID' in os.environ:
        del os.environ['CLAUDE_AGENT_ID']


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_subprocess():
    """Mock subprocess.run for screen command testing."""
    with patch('subprocess.run') as mock_run:
        # Default successful screen command response
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = ""
        yield mock_run


@pytest.fixture
def mock_screen_session():
    """Mock screen session for testing without actual screen dependency."""
    session_data = {
        'name': 'test-session',
        'status': 'running',
        'exit_code': None,
        'output': 'Mock session output\n',
        'created': True
    }
    
    def mock_create_session(name: str, command: str, working_dir: Optional[str] = None):
        session_data['name'] = name
        session_data['command'] = command
        session_data['working_dir'] = working_dir
        return {'success': True, 'session_name': name, 'status': 'running'}
    
    def mock_get_status(name: str):
        return {
            'session_name': name,
            'status': session_data['status'],
            'exit_code': session_data['exit_code'],
            'is_running': session_data['status'] == 'running'
        }
    
    def mock_set_completed(exit_code: int = 0):
        session_data['status'] = 'completed' if exit_code == 0 else 'error'
        session_data['exit_code'] = exit_code
    
    mock_session = Mock()
    mock_session.create_session = mock_create_session
    mock_session.get_session_status = mock_get_status
    mock_session.set_completed = mock_set_completed
    mock_session.data = session_data
    
    return mock_session


@pytest.fixture
def mock_screen_commands():
    """Mock screen command responses for realistic testing."""
    
    def mock_subprocess_run(cmd, *args, **kwargs):
        result = Mock()
        result.returncode = 0
        result.stdout = ""
        result.stderr = ""
        
        if 'screen' in cmd and '-ls' in cmd:
            # Mock screen -ls output
            result.stdout = "There are screens on:\n\t12345.test-agent-abc123-session\t(Detached)\n1 Socket in /tmp/screens/S-user.\n"
        elif 'screen' in cmd and '-dmS' in cmd:
            # Mock screen session creation
            result.returncode = 0
        elif 'screen' in cmd and '-S' in cmd and 'stuff' in cmd:
            # Mock sending commands to screen
            result.returncode = 0
        elif 'screen' in cmd and '--version' in cmd:
            # Mock screen version
            result.stdout = "Screen version 4.09.00 (GNU) 30-Jan-22"
        
        return result
    
    with patch('subprocess.run', side_effect=mock_subprocess_run) as mock_run:
        yield mock_run


@pytest.fixture
def sample_exit_code_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create sample exit code file for testing."""
    exit_file = temp_dir / "test-session.exit"
    exit_file.write_text("EXIT_CODE:0\n")
    yield exit_file


@pytest.fixture
def sample_output_file(temp_dir: Path) -> Generator[Path, None, None]:
    """Create sample output file for testing."""
    output_file = temp_dir / "test-session.out"
    output_file.write_text("Hello World\nTest output line 2\nCompleted successfully\n")
    yield output_file


@pytest.fixture
def mock_ipdb():
    """Mock ipdb for testing conditional debugging."""
    with patch('screen_manager.cipdb.ipdb') as mock_ipdb_module:
        mock_ipdb_module.set_trace = Mock()
        mock_ipdb_module.post_mortem = Mock()
        yield mock_ipdb_module


@pytest.fixture
def mock_fastmcp():
    """Mock FastMCP for testing MCP server."""
    with patch('screen_manager.mcp_server.FastMCP') as mock_mcp_class:
        mock_mcp = Mock()
        mock_mcp_class.return_value = mock_mcp
        mock_mcp.tool = Mock(return_value=lambda f: f)  # Decorator passthrough
        mock_mcp.run = Mock()
        mock_mcp.run_http = Mock()
        mock_mcp.run_sse = Mock()
        yield mock_mcp


@pytest.fixture
def condition_test_data() -> Dict[str, Any]:
    """Sample data for condition evaluation testing."""
    return {
        'bool_conditions': [True, False],
        'string_conditions': ['AGENT_ID', 'NONEXISTENT_VAR', 'len(AGENT_ID) > 5'],
        'callable_conditions': [
            lambda: True,
            lambda: False,
            lambda: os.environ.get('TEST_FLAG') == 'true'
        ],
        'dict_conditions': [
            {'AGENT_ID': 'test-agent'},
            {'CLAUDE_AGENT_ID': 'claude-test'},
            {'NONEXISTENT': 'value'}
        ]
    }


@pytest.fixture
def mcp_tools_test_data() -> Dict[str, Any]:
    """Sample data for MCP tools testing."""
    return {
        'session_name': 'test-debug-session',
        'command': 'python -c "print(\\"test\\"); exit(0)"',
        'working_dir': '/tmp/test',
        'timeout': 10,
        'lines': 5
    }


# Performance testing utilities
@pytest.fixture
def performance_threshold() -> Dict[str, float]:
    """Performance thresholds for different operations."""
    return {
        'agent_id_detection': 0.001,  # 1ms
        'condition_evaluation': 0.001,  # 1ms  
        'session_status_check': 0.1,   # 100ms
        'mcp_tool_response': 0.5,      # 500ms
        'session_creation': 1.0        # 1 second
    }


# Markers for test categories
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests") 
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow tests (> 1 second)")
    config.addinivalue_line("markers", "requires_screen: Tests requiring screen command")


# Utility functions for tests
def assert_agent_id_format(agent_id: str) -> None:
    """Assert agent ID follows expected format."""
    assert isinstance(agent_id, str)
    assert len(agent_id) > 0
    # Should be UUID-like or recognizable format
    assert '-' in agent_id or len(agent_id) >= 8


def assert_session_info_complete(session_info: Dict[str, Any]) -> None:
    """Assert session info contains expected fields."""
    required_fields = ['session_name', 'status', 'exit_code', 'is_running']
    for field in required_fields:
        assert field in session_info, f"Missing required field: {field}"
    
    assert session_info['status'] in ['running', 'completed', 'error', 'unknown']
    if session_info['exit_code'] is not None:
        assert isinstance(session_info['exit_code'], int)


def assert_mcp_tool_response(response: Dict[str, Any], success_expected: bool = True) -> None:
    """Assert MCP tool response format."""
    if success_expected:
        assert response.get('success', True) is not False
    else:
        assert 'error' in response or response.get('success') is False