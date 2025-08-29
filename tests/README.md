# Screen Session Manager - Test Suite

Comprehensive test suite for the screen-manager project, following the v05 simplified architecture and test-driven development principles.

## Test Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                 # Shared fixtures and configuration
├── run_tests.py               # Test runner script with quality gates
├── README.md                  # This file
│
├── unit/                      # Unit tests for individual components
│   ├── test_cipdb.py         # Conditional iPDB functionality  
│   ├── test_screen_manager.py  # Session management
│   ├── test_mcp_server.py    # MCP tools and server
│   └── test_cli.py           # Command line interface
│
├── integration/               # End-to-end integration tests
│   └── test_end_to_end.py    # Complete workflows and scenarios
│
├── mocks/                     # Mock utilities for testing
│   ├── __init__.py
│   └── screen_mock.py        # Screen session mocking
│
├── fixtures/                  # Test data and fixtures
│   ├── __init__.py
│   └── sample_data.py        # Sample test data and scenarios
│
├── test_performance.py       # Performance and benchmark tests
└── reports/                  # Generated test reports
    ├── htmlcov/              # HTML coverage reports
    ├── coverage.json         # Coverage data
    └── coverage_badge.json   # Coverage badge info
```

## Test Categories

### Unit Tests (`tests/unit/`)

- **`test_cipdb.py`**: Tests conditional debugging functionality
  - Agent ID detection and generation
  - Condition evaluation (boolean, string, callable, dict)
  - Conditional breakpoint triggering
  - Debug decorators and convenience functions
  - Performance requirements (sub-millisecond response)

- **`test_screen_manager.py`**: Tests session management
  - Session creation and lifecycle management
  - Status monitoring and exit code handling
  - Command sending and output capture
  - Session cleanup and resource management
  - Error handling and edge cases

- **`test_mcp_server.py`**: Tests MCP server tools
  - All 9 MCP tools for agent coordination
  - FastMCP integration and server management
  - Tool response format validation
  - Error handling and timeout scenarios
  - Agent information and coordination

- **`test_cli.py`**: Tests command-line interface
  - Serve, debug, and info commands
  - Argument parsing and validation
  - Integration with underlying components
  - Error handling and help output

### Integration Tests (`tests/integration/`)

- **`test_end_to_end.py`**: Complete workflow testing
  - End-to-end debugging session workflows
  - Multi-agent coordination scenarios
  - Error recovery and handling
  - Performance in integrated scenarios
  - Real-world debugging use cases

### Performance Tests (`tests/test_performance.py`)

- Response time validation (sub-second requirements)
- Throughput benchmarking
- Memory usage monitoring
- Scalability testing with multiple agents
- Performance regression baseline

### Mock Utilities (`tests/mocks/`)

- **`screen_mock.py`**: Comprehensive screen session mocking
  - Realistic session behavior simulation
  - Command execution and output generation
  - Exit code and timing simulation
  - Context manager for easy testing

### Test Fixtures (`tests/fixtures/`)

- **`sample_data.py`**: Rich test data and scenarios
  - Sample agent configurations
  - Debugging scenarios and conditions
  - MCP workflow patterns
  - Performance benchmarks
  - Error scenarios and recovery patterns

## Running Tests

### Quick Start

```bash
# Run full test suite with all quality gates
python tests/run_tests.py

# Run with verbose output
python tests/run_tests.py --verbose

# Run specific test categories
python tests/run_tests.py --unit
python tests/run_tests.py --integration
python tests/run_tests.py --performance

# Run smoke tests for CI
python tests/run_tests.py --smoke
```

### Using Pytest Directly

```bash
# Unit tests with coverage
pytest tests/unit/ --cov=src/screen_manager --cov-report=term-missing

# Integration tests
pytest tests/integration/ -m integration

# Performance tests
pytest tests/test_performance.py -m performance -v -s

# Specific test file
pytest tests/unit/test_cipdb.py -v

# Specific test class or method
pytest tests/unit/test_cipdb.py::TestGetAgentId::test_get_agent_id_from_claude_agent_id -v
```

### Test Markers

Tests are organized with pytest markers:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests  
- `@pytest.mark.performance`: Performance benchmarks
- `@pytest.mark.slow`: Tests taking > 1 second
- `@pytest.mark.requires_screen`: Tests requiring screen command

```bash
# Run only fast tests
pytest -m "not slow"

# Run performance tests
pytest -m performance

# Run unit tests only
pytest -m unit
```

## Test Philosophy

Following the project's test-driven development philosophy:

### 1. Specification-Driven Testing
- Tests written based on architectural specifications
- Focus on behavioral verification, not just code coverage
- One-to-one relationship between features and test coverage

### 2. Quality Gates
- **95%+ code coverage** requirement
- **Sub-second response times** for core operations
- **Zero linting errors** with ruff
- **Type safety** validation with mypy
- **All tests passing** before commits

### 3. Independent and Mockable
- Tests run without external dependencies
- Screen commands fully mocked for reliability
- Isolated test environments with clean fixtures
- Fast test execution for rapid development cycles

### 4. Multi-Agent Focus
- Test scenarios designed for multi-agent debugging
- Agent isolation and coordination testing
- Conditional debugging validation
- Performance under concurrent agent load

## Coverage Requirements

The test suite maintains **95%+ coverage** across all components:

- **cipdb.py**: Agent ID detection, condition evaluation, debugging triggers
- **screen_manager.py**: Session lifecycle, status monitoring, exit codes
- **mcp_server.py**: All MCP tools and server functionality
- **cli.py**: Command parsing and execution

Coverage reports are generated in multiple formats:
- Terminal output with missing lines
- HTML report (`tests/reports/htmlcov/`)
- JSON data (`tests/reports/coverage.json`)

## Performance Requirements

Core operations must meet strict performance requirements:

- **Agent ID detection**: < 1ms
- **Condition evaluation**: < 1ms  
- **Session status check**: < 100ms
- **MCP tool response**: < 500ms
- **Session creation**: < 1 second

Performance tests validate these requirements and track regressions.

## Fixtures and Utilities

### Shared Fixtures (`conftest.py`)

- `temp_agent_id`: Generate unique agent IDs
- `clean_env`: Clean environment variables
- `set_agent_env`: Set agent environment variables
- `mock_screen_session`: Mock session functionality
- `mock_subprocess`: Mock screen commands
- `performance_threshold`: Performance requirement data

### Mock Utilities (`mocks/screen_mock.py`)

- `MockScreenSession`: Individual session simulation
- `MockScreenManager`: Complete screen environment
- `ScreenMockContext`: Context manager for mocking
- `create_mock_screen_environment()`: Easy mock setup

### Sample Data (`fixtures/sample_data.py`)

- Agent configurations and scenarios
- Session workflow patterns
- Debugging conditions and triggers
- Performance benchmarks
- Error scenarios and recovery

## Continuous Integration

The test suite is designed for CI/CD integration:

### Quality Gates Validation
```bash
# Full quality gate check
python tests/run_tests.py

# Skip specific gates for faster feedback
python tests/run_tests.py --skip-performance --skip-types
```

### Smoke Tests for Fast Feedback
```bash
# Quick validation (~30 seconds)
python tests/run_tests.py --smoke
```

### Test Reports
- HTML coverage reports for detailed analysis
- JSON coverage data for CI integration
- Performance benchmarks for regression tracking

## Development Workflow

### Adding New Tests

1. **Unit Tests**: Add to appropriate `tests/unit/test_*.py` file
2. **Integration Tests**: Add to `tests/integration/test_end_to_end.py`
3. **Performance Tests**: Add to `tests/test_performance.py`
4. **Sample Data**: Add scenarios to `tests/fixtures/sample_data.py`

### Test-Driven Development

1. Write failing tests based on specifications
2. Implement minimal code to pass tests
3. Refactor while keeping tests green
4. Ensure all quality gates pass before commit

### Before Committing

```bash
# Verify all quality gates
python tests/run_tests.py

# Check specific issues
python tests/run_tests.py --unit --verbose
ruff check src/ tests/
mypy src/screen_manager/
```

## Troubleshooting

### Common Issues

- **Screen command not found**: Tests use mocking, no actual screen needed
- **Permission errors**: Check file permissions on test runner
- **Coverage below 95%**: Add tests for uncovered code paths
- **Performance test failures**: Check system load, adjust thresholds if needed

### Debug Test Failures

```bash
# Run with full output and no capture
pytest tests/unit/test_cipdb.py::TestGetAgentId -v -s --tb=long

# Run single test with debugging
pytest tests/unit/test_cipdb.py::TestGetAgentId::test_get_agent_id_from_claude_agent_id -v -s --pdb
```

### Mock Debugging

```bash
# Enable mock call history
import logging
logging.getLogger('tests.mocks').setLevel(logging.DEBUG)
```

## Contributing

When adding new functionality:

1. **Write tests first** based on specifications
2. **Follow naming conventions** (`test_feature_name_scenario`)
3. **Use appropriate markers** (`@pytest.mark.unit`, etc.)
4. **Mock external dependencies** (screen, subprocess, etc.)
5. **Verify performance requirements** for new code paths
6. **Update sample data** if adding new scenarios
7. **Maintain 95%+ coverage** requirement

The test suite is a critical component ensuring the reliability and performance of the screen-manager for multi-agent debugging scenarios.