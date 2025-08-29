#!/usr/bin/env python3
"""
Sample test data and fixtures for screen-manager tests.

Provides realistic test scenarios, sample configurations, and test data
for comprehensive testing of all components.
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta


# Agent test data
SAMPLE_AGENTS = {
    'claude_agents': [
        'claude-test-agent-1',
        'claude-debug-agent-2', 
        'claude-prod-agent-3'
    ],
    'generic_agents': [
        'test-agent-alpha',
        'debug-agent-beta',
        'monitor-agent-gamma'
    ],
    'priority_agents': {
        'high': ['critical-debug-agent', 'prod-monitor-agent'],
        'medium': ['dev-test-agent', 'integration-agent'],
        'low': ['experimental-agent', 'learning-agent']
    }
}


# Sample session configurations
SAMPLE_SESSION_CONFIGS = [
    {
        'name': 'python-debug',
        'command': 'python -c "import time; print(\\"Starting\\"); time.sleep(1); print(\\"Done\\")"',
        'working_dir': '/tmp/debug',
        'expected_duration': 1.5,
        'expected_exit_code': 0,
        'expected_output': ['Starting', 'Done']
    },
    {
        'name': 'error-session',
        'command': 'python -c "import sys; print(\\"Error test\\"); sys.exit(1)"',
        'working_dir': '/tmp/error',
        'expected_duration': 0.5,
        'expected_exit_code': 1,
        'expected_output': ['Error test']
    },
    {
        'name': 'long-running',
        'command': 'python -c "import time; [print(f\\"Step {i}\\") or time.sleep(0.1) for i in range(5)]"',
        'working_dir': '/tmp/long',
        'expected_duration': 1.0,
        'expected_exit_code': 0,
        'expected_output': ['Step 0', 'Step 1', 'Step 2', 'Step 3', 'Step 4']
    },
    {
        'name': 'interactive-session',
        'command': 'python -i -c "print(\\"Interactive mode ready\\")"',
        'working_dir': '/tmp/interactive',
        'expected_duration': None,  # Long-running
        'expected_exit_code': None,  # Still running
        'expected_output': ['Interactive mode ready', '>>>']
    }
]


# Sample debugging scenarios
DEBUGGING_SCENARIOS = [
    {
        'name': 'conditional_debug_by_agent',
        'description': 'Debug only specific agent',
        'condition': {'type': 'agent_id', 'value': 'debug-target-agent'},
        'expected_debug': True,
        'test_agents': ['debug-target-agent', 'other-agent', 'third-agent']
    },
    {
        'name': 'conditional_debug_by_env',
        'description': 'Debug based on environment variable',
        'condition': {'type': 'env_var', 'var': 'DEBUG_MODE', 'value': 'enabled'},
        'expected_debug': True,
        'environment': {'DEBUG_MODE': 'enabled', 'LOG_LEVEL': 'debug'}
    },
    {
        'name': 'conditional_debug_complex',
        'description': 'Complex condition with multiple factors',
        'condition': {
            'type': 'expression', 
            'expr': 'AGENT_ID.startswith("debug") and DEBUG_LEVEL == "verbose"'
        },
        'expected_debug': True,
        'environment': {'DEBUG_LEVEL': 'verbose'},
        'test_agents': ['debug-special-agent', 'prod-normal-agent']
    }
]


# Sample MCP tool scenarios
MCP_SCENARIOS = [
    {
        'name': 'single_session_workflow',
        'description': 'Create, monitor, and cleanup single session',
        'steps': [
            {'action': 'create', 'params': {'name': 'workflow-test', 'command': 'python simple.py'}},
            {'action': 'status', 'params': {'name': 'workflow-test'}},
            {'action': 'wait', 'params': {'name': 'workflow-test', 'timeout': 5}},
            {'action': 'output', 'params': {'name': 'workflow-test', 'lines': 10}},
            {'action': 'cleanup', 'params': {'name': 'workflow-test'}}
        ],
        'expected_results': [
            {'success': True, 'status': 'running'},
            {'status': 'running', 'is_running': True},
            {'success': True, 'status': 'completed'},
            {'output': 'simple.py output'},
            {'success': True}
        ]
    },
    {
        'name': 'multi_session_coordination',
        'description': 'Multiple agents coordinating sessions',
        'agents': ['coordinator-agent', 'worker-agent-1', 'worker-agent-2'],
        'sessions': [
            {'agent': 'coordinator-agent', 'name': 'main-task', 'command': 'python coordinator.py'},
            {'agent': 'worker-agent-1', 'name': 'worker-1', 'command': 'python worker1.py'},
            {'agent': 'worker-agent-2', 'name': 'worker-2', 'command': 'python worker2.py'}
        ],
        'coordination_steps': [
            {'agent': 'coordinator-agent', 'action': 'send_command', 'target': 'main-task', 'command': 'start_workers()'},
            {'agent': 'worker-agent-1', 'action': 'status', 'target': 'worker-1'},
            {'agent': 'worker-agent-2', 'action': 'status', 'target': 'worker-2'},
            {'agent': 'coordinator-agent', 'action': 'wait', 'target': 'main-task'}
        ]
    },
    {
        'name': 'error_handling_scenario',
        'description': 'Handle various error conditions',
        'error_cases': [
            {'type': 'session_creation_failure', 'expected_error': 'Screen command failed'},
            {'type': 'session_not_found', 'expected_error': 'Session not found'},
            {'type': 'command_send_failure', 'expected_error': 'Session not running'},
            {'type': 'timeout_scenario', 'expected_error': 'Timeout exceeded'}
        ]
    }
]


# CLI test scenarios
CLI_TEST_SCENARIOS = [
    {
        'name': 'serve_stdio',
        'command': ['serve'],
        'expected_transport': 'stdio',
        'expected_host': 'localhost',
        'expected_port': 8080
    },
    {
        'name': 'serve_http',
        'command': ['serve', '--transport', 'http', '--port', '9000'],
        'expected_transport': 'http',
        'expected_host': 'localhost', 
        'expected_port': 9000
    },
    {
        'name': 'debug_create_wait_cleanup',
        'command': [
            'debug', '--name', 'cli-test', '--command', 'python test_script.py',
            '--create', '--wait', '--timeout', '10', '--cleanup'
        ],
        'expected_actions': ['create', 'wait', 'cleanup']
    },
    {
        'name': 'debug_list_sessions',
        'command': ['debug', '--list'],
        'expected_actions': ['list']
    },
    {
        'name': 'info_system',
        'command': ['info'],
        'expected_info': ['agent_id', 'screen_version', 'python_version', 'environment_variables']
    }
]


# Performance test data
PERFORMANCE_BENCHMARKS = {
    'response_times': {
        'agent_id_detection': {'target': 0.001, 'max_acceptable': 0.01},
        'condition_evaluation': {'target': 0.001, 'max_acceptable': 0.01},
        'session_status_check': {'target': 0.1, 'max_acceptable': 0.5},
        'mcp_tool_response': {'target': 0.5, 'max_acceptable': 2.0},
        'session_creation': {'target': 1.0, 'max_acceptable': 5.0}
    },
    'throughput': {
        'status_checks_per_second': {'target': 100, 'min_acceptable': 20},
        'condition_evaluations_per_second': {'target': 1000, 'min_acceptable': 100},
        'agent_id_retrievals_per_second': {'target': 1000, 'min_acceptable': 100}
    },
    'scalability': {
        'max_concurrent_sessions': {'target': 50, 'min_acceptable': 10},
        'max_agents_simultaneously': {'target': 20, 'min_acceptable': 5}
    }
}


# Sample environment configurations
ENVIRONMENT_CONFIGS = [
    {
        'name': 'development',
        'variables': {
            'CLAUDE_AGENT_ID': 'dev-agent-123',
            'DEBUG_MODE': 'enabled',
            'LOG_LEVEL': 'debug',
            'TESTING': 'true'
        }
    },
    {
        'name': 'production',
        'variables': {
            'CLAUDE_AGENT_ID': 'prod-agent-456',
            'DEBUG_MODE': 'disabled',
            'LOG_LEVEL': 'info',
            'TESTING': 'false'
        }
    },
    {
        'name': 'testing',
        'variables': {
            'CLAUDE_AGENT_ID': 'test-agent-789',
            'DEBUG_MODE': 'conditional',
            'LOG_LEVEL': 'debug',
            'TESTING': 'true',
            'TEST_COVERAGE': 'enabled'
        }
    }
]


def create_sample_session_data(agent_id: str, count: int = 5) -> List[Dict[str, Any]]:
    """Generate sample session data for testing."""
    sessions = []
    base_time = datetime.now()
    
    for i in range(count):
        session = {
            'name': f"{agent_id}-session-{i}",
            'command': f"python task_{i}.py",
            'working_dir': f"/tmp/task_{i}",
            'created_at': (base_time + timedelta(minutes=i)).isoformat(),
            'status': 'completed' if i < count - 1 else 'running',
            'exit_code': 0 if i < count - 1 else None,
            'agent_id': agent_id,
            'duration': i + 1.0,
            'output_lines': [f"Task {i} output line {j}" for j in range(5)]
        }
        sessions.append(session)
    
    return sessions


def create_sample_output_file(content_lines: List[str], temp_dir: Optional[Path] = None) -> Path:
    """Create a temporary file with sample output content."""
    if temp_dir is None:
        temp_dir = Path(tempfile.gettempdir())
    
    output_file = temp_dir / f"sample_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.out"
    
    with open(output_file, 'w') as f:
        for line in content_lines:
            f.write(f"{line}\n")
    
    return output_file


def create_sample_exit_code_file(exit_code: int, temp_dir: Optional[Path] = None) -> Path:
    """Create a temporary exit code file."""
    if temp_dir is None:
        temp_dir = Path(tempfile.gettempdir())
    
    exit_file = temp_dir / f"sample_exit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.exit"
    
    with open(exit_file, 'w') as f:
        f.write(f"EXIT_CODE:{exit_code}\n")
    
    return exit_file


def generate_screen_ls_output(sessions: List[Dict[str, Any]]) -> str:
    """Generate realistic screen -ls output."""
    if not sessions:
        return "No Sockets found in /tmp/screens/S-user.\n"
    
    lines = ["There are screens on:"]
    
    for i, session in enumerate(sessions, start=12345):
        status = "(Attached)" if session.get('is_attached', False) else "(Detached)"
        lines.append(f"\t{i}.{session['name']}\t{status}")
    
    socket_count = len(sessions)
    lines.append(f"{socket_count} Socket{'s' if socket_count != 1 else ''} in /tmp/screens/S-user.")
    
    return '\n'.join(lines) + '\n'


def create_complex_debugging_scenario() -> Dict[str, Any]:
    """Create a complex multi-agent debugging scenario."""
    return {
        'name': 'multi_agent_complex_debug',
        'description': 'Complex scenario with multiple agents, conditions, and workflows',
        'agents': {
            'primary': {
                'id': 'primary-debug-agent',
                'role': 'coordinator',
                'sessions': ['main-workflow', 'status-monitor'],
                'debug_conditions': ['AGENT_ID == "primary-debug-agent"', 'DEBUG_PRIMARY == "true"']
            },
            'secondary': {
                'id': 'secondary-worker-agent',
                'role': 'worker',
                'sessions': ['worker-task-1', 'worker-task-2'],
                'debug_conditions': ['DEBUG_SECONDARY == "enabled"']
            },
            'monitor': {
                'id': 'monitor-oversight-agent',
                'role': 'monitor',
                'sessions': ['system-monitor'],
                'debug_conditions': ['MONITOR_DEBUG == "verbose"']
            }
        },
        'workflow_steps': [
            {'step': 1, 'agent': 'primary', 'action': 'create_session', 'session': 'main-workflow'},
            {'step': 2, 'agent': 'secondary', 'action': 'create_session', 'session': 'worker-task-1'},
            {'step': 3, 'agent': 'secondary', 'action': 'create_session', 'session': 'worker-task-2'},
            {'step': 4, 'agent': 'monitor', 'action': 'create_session', 'session': 'system-monitor'},
            {'step': 5, 'agent': 'primary', 'action': 'coordinate_workers', 'targets': ['worker-task-1', 'worker-task-2']},
            {'step': 6, 'agent': 'monitor', 'action': 'monitor_all', 'targets': ['main-workflow', 'worker-task-1', 'worker-task-2']},
            {'step': 7, 'agent': 'primary', 'action': 'wait_completion', 'session': 'main-workflow'},
            {'step': 8, 'agent': 'primary', 'action': 'cleanup_all'}
        ],
        'expected_outcomes': {
            'sessions_created': 4,
            'debug_triggers': {'primary': 1, 'secondary': 0, 'monitor': 0},  # Only primary should debug
            'coordination_messages': 3,
            'total_duration': 10.0,
            'success_rate': 1.0
        },
        'environment': {
            'DEBUG_PRIMARY': 'true',
            'DEBUG_SECONDARY': 'disabled',
            'MONITOR_DEBUG': 'info'
        }
    }


# Sample error scenarios for comprehensive testing
ERROR_SCENARIOS = [
    {
        'name': 'screen_command_not_found',
        'error_type': 'FileNotFoundError',
        'error_message': 'screen command not found',
        'recovery_strategy': 'provide_helpful_error_message'
    },
    {
        'name': 'session_creation_permission_denied',
        'error_type': 'PermissionError', 
        'error_message': 'Permission denied creating screen session',
        'recovery_strategy': 'suggest_permission_fix'
    },
    {
        'name': 'session_already_exists',
        'error_type': 'ValueError',
        'error_message': 'Session with name already exists',
        'recovery_strategy': 'suggest_different_name'
    },
    {
        'name': 'invalid_command_syntax',
        'error_type': 'SyntaxError',
        'error_message': 'Invalid command syntax',
        'recovery_strategy': 'validate_command_before_execution'
    },
    {
        'name': 'timeout_exceeded',
        'error_type': 'TimeoutError',
        'error_message': 'Operation timed out',
        'recovery_strategy': 'provide_timeout_options'
    }
]


def get_sample_data(category: str) -> Any:
    """Get sample data by category."""
    categories = {
        'agents': SAMPLE_AGENTS,
        'sessions': SAMPLE_SESSION_CONFIGS,
        'debugging': DEBUGGING_SCENARIOS,
        'mcp': MCP_SCENARIOS,
        'cli': CLI_TEST_SCENARIOS,
        'performance': PERFORMANCE_BENCHMARKS,
        'environments': ENVIRONMENT_CONFIGS,
        'errors': ERROR_SCENARIOS
    }
    
    return categories.get(category, {})


if __name__ == "__main__":
    # Demo usage of sample data
    print("Screen Session Manager - Sample Test Data")
    print("=" * 50)
    
    print(f"Available agent types: {list(SAMPLE_AGENTS.keys())}")
    print(f"Sample session configs: {len(SAMPLE_SESSION_CONFIGS)}")
    print(f"Debugging scenarios: {len(DEBUGGING_SCENARIOS)}")
    print(f"MCP scenarios: {len(MCP_SCENARIOS)}")
    print(f"CLI scenarios: {len(CLI_TEST_SCENARIOS)}")
    print(f"Performance benchmarks: {len(PERFORMANCE_BENCHMARKS)}")
    
    # Generate sample session data
    sample_sessions = create_sample_session_data("demo-agent", 3)
    print(f"\nGenerated {len(sample_sessions)} sample sessions")
    
    # Generate screen output
    screen_output = generate_screen_ls_output(sample_sessions)
    print(f"\nSample screen -ls output:\n{screen_output}")
    
    # Show complex scenario
    complex_scenario = create_complex_debugging_scenario()
    print(f"\nComplex scenario has {len(complex_scenario['agents'])} agents")
    print(f"and {len(complex_scenario['workflow_steps'])} workflow steps")