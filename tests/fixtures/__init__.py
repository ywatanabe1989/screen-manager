"""Test fixtures and sample data for screen-manager."""

from .sample_data import (
    SAMPLE_AGENTS,
    SAMPLE_SESSION_CONFIGS,
    DEBUGGING_SCENARIOS,
    MCP_SCENARIOS,
    CLI_TEST_SCENARIOS,
    PERFORMANCE_BENCHMARKS,
    ENVIRONMENT_CONFIGS,
    ERROR_SCENARIOS,
    create_sample_session_data,
    create_sample_output_file,
    create_sample_exit_code_file,
    generate_screen_ls_output,
    create_complex_debugging_scenario,
    get_sample_data
)

__all__ = [
    'SAMPLE_AGENTS',
    'SAMPLE_SESSION_CONFIGS',
    'DEBUGGING_SCENARIOS',
    'MCP_SCENARIOS',
    'CLI_TEST_SCENARIOS',
    'PERFORMANCE_BENCHMARKS',
    'ENVIRONMENT_CONFIGS',
    'ERROR_SCENARIOS',
    'create_sample_session_data',
    'create_sample_output_file',
    'create_sample_exit_code_file',
    'generate_screen_ls_output',
    'create_complex_debugging_scenario',
    'get_sample_data'
]