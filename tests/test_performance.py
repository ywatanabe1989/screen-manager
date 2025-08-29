#!/usr/bin/env python3
"""
Performance tests for screen-manager components.

Tests sub-second response time requirements for all core functionality
including agent identification, session management, and MCP tools.
"""

import time
import statistics
from unittest.mock import Mock, patch
from typing import List, Dict, Any, Callable

import pytest

from screen_manager.cipdb import get_agent_id, check_condition, set_trace
from screen_manager.screen_manager import ScreenSessionManager
from screen_manager.mcp_server import (
    create_debug_session, get_session_status, send_command,
    get_exit_code, wait_for_completion, get_session_output
)
from screen_manager.cli import main
from tests.mocks import create_mock_screen_environment


def measure_performance(func: Callable, iterations: int = 100) -> Dict[str, float]:
    """
    Measure performance of a function over multiple iterations.
    
    Args:
        func: Function to measure
        iterations: Number of iterations to run
        
    Returns:
        Performance statistics
    """
    times = []
    
    for _ in range(iterations):
        start_time = time.time()
        func()
        end_time = time.time()
        times.append(end_time - start_time)
    
    return {
        'min': min(times),
        'max': max(times),
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0.0,
        'p95': sorted(times)[int(0.95 * len(times))],
        'total': sum(times)
    }


@pytest.mark.performance
class TestCipdbPerformance:
    """Performance tests for cipdb functionality."""
    
    def test_get_agent_id_performance(self, performance_threshold, set_agent_env):
        """Test agent ID retrieval performance."""
        def get_id():
            return get_agent_id()
        
        stats = measure_performance(get_id, iterations=1000)
        
        # Should be very fast (sub-millisecond)
        assert stats['mean'] < performance_threshold['agent_id_detection']
        assert stats['p95'] < performance_threshold['agent_id_detection'] * 2
        assert stats['max'] < 0.01  # No single call should exceed 10ms
    
    def test_check_condition_performance(self, performance_threshold):
        """Test condition checking performance for different condition types."""
        test_cases = [
            ('boolean_true', lambda: check_condition(True)),
            ('boolean_false', lambda: check_condition(False)),
            ('string_env', lambda: check_condition('AGENT_ID')),
            ('callable', lambda: check_condition(lambda: True)),
            ('dict_condition', lambda: check_condition({'AGENT_ID': 'test'}))
        ]
        
        for condition_type, test_func in test_cases:
            stats = measure_performance(test_func, iterations=1000)
            
            # All condition types should be very fast
            assert stats['mean'] < performance_threshold['condition_evaluation'], \
                f"Condition type {condition_type} too slow: {stats['mean']:.6f}s"
            
            assert stats['p95'] < performance_threshold['condition_evaluation'] * 2, \
                f"Condition type {condition_type} 95th percentile too slow: {stats['p95']:.6f}s"
    
    def test_set_trace_performance_false_condition(self, performance_threshold):
        """Test set_trace performance when condition is False (no debugging)."""
        with patch('screen_manager.cipdb.ipdb'):
            def no_debug_trace():
                set_trace(condition=False)
            
            stats = measure_performance(no_debug_trace, iterations=1000)
            
            # When not debugging, should be extremely fast
            assert stats['mean'] < performance_threshold['condition_evaluation']
            assert stats['p95'] < performance_threshold['condition_evaluation'] * 2
    
    def test_condition_evaluation_scaling(self):
        """Test condition evaluation performance with complex conditions."""
        # Test increasingly complex conditions
        conditions = [
            'True',  # Simple
            'AGENT_ID and len(AGENT_ID) > 0',  # Medium
            'AGENT_ID and len(AGENT_ID) > 5 and "agent" in AGENT_ID.lower()',  # Complex
        ]
        
        with patch.dict('os.environ', {'AGENT_ID': 'test-agent-12345'}):
            for i, condition in enumerate(conditions, 1):
                def test_condition():
                    check_condition(condition)
                
                stats = measure_performance(test_condition, iterations=500)
                
                # Even complex conditions should be fast
                assert stats['mean'] < 0.001, f"Condition {i} too slow: {stats['mean']:.6f}s"


@pytest.mark.performance
class TestSessionManagerPerformance:
    """Performance tests for ScreenSessionManager."""
    
    def test_session_creation_performance(self, performance_threshold):
        """Test session creation performance."""
        manager = ScreenSessionManager(agent_id="perf-test-agent")
        
        with create_mock_screen_environment():
            def create_session():
                return manager.create_session(
                    "perf-test",
                    "python -c 'print(\"test\")'"
                )
            
            stats = measure_performance(create_session, iterations=50)
            
            # Session creation should meet performance threshold
            assert stats['mean'] < performance_threshold['session_creation']
            assert stats['p95'] < performance_threshold['session_creation'] * 1.5
    
    def test_session_status_check_performance(self, performance_threshold):
        """Test session status checking performance."""
        manager = ScreenSessionManager(agent_id="perf-test-agent")
        
        with create_mock_screen_environment() as mock_screen:
            # Create a test session
            mock_screen.create_session("perf-status-test", "python test.py")
            
            def check_status():
                return manager.get_session_status("perf-status-test")
            
            stats = measure_performance(check_status, iterations=200)
            
            # Status checks should be fast
            assert stats['mean'] < performance_threshold['session_status_check']
            assert stats['p95'] < performance_threshold['session_status_check'] * 2
    
    def test_multiple_session_management_performance(self):
        """Test performance with multiple concurrent sessions."""
        manager = ScreenSessionManager(agent_id="perf-multi-agent")
        session_count = 10
        
        with create_mock_screen_environment():
            # Create multiple sessions
            session_names = []
            start_time = time.time()
            
            for i in range(session_count):
                name = f"multi-perf-{i}"
                result = manager.create_session(name, f"python task_{i}.py")
                assert result['success']
                session_names.append(name)
            
            creation_time = time.time() - start_time
            
            # Should create 10 sessions quickly
            assert creation_time < 2.0, f"Creating {session_count} sessions took {creation_time:.3f}s"
            
            # Check all statuses quickly
            start_time = time.time()
            
            for name in session_names:
                status = manager.get_session_status(name)
                assert status['session_name'].endswith(name)
            
            status_check_time = time.time() - start_time
            
            # Should check all statuses quickly
            assert status_check_time < 1.0, f"Checking {session_count} statuses took {status_check_time:.3f}s"
    
    def test_session_cleanup_performance(self):
        """Test session cleanup performance."""
        manager = ScreenSessionManager(agent_id="perf-cleanup-agent")
        
        with create_mock_screen_environment() as mock_screen:
            # Create sessions to clean up
            session_names = [f"cleanup-{i}" for i in range(5)]
            
            for name in session_names:
                mock_screen.create_session(f"perf-cleanup-agent-{name}", "python test.py")
            
            def cleanup_all():
                for name in session_names:
                    result = manager.cleanup_session(name)
                    assert result is True
            
            stats = measure_performance(cleanup_all, iterations=10)
            
            # Cleanup should be reasonably fast
            assert stats['mean'] < 1.0  # 1 second for 5 sessions
            assert stats['max'] < 2.0   # No single cleanup should exceed 2 seconds


@pytest.mark.performance
class TestMCPToolsPerformance:
    """Performance tests for MCP tools."""
    
    def test_mcp_tool_response_times(self, performance_threshold):
        """Test all MCP tools meet response time requirements."""
        mcp_tools = [
            (create_debug_session, ("test", "python script.py")),
            (get_session_status, ("test-session",)),
            (send_command, ("test-session", "print('test')")),
            (get_exit_code, ("test-session",)),
            (get_session_output, ("test-session",))
        ]
        
        with patch('screen_manager.mcp_server.get_session_manager') as mock_get_manager:
            # Setup fast mock responses
            mock_manager = Mock()
            mock_manager.create_session.return_value = {'success': True}
            mock_manager.get_session_status.return_value = {'status': 'running'}
            mock_manager.send_command.return_value = {'success': True}
            mock_manager.get_exit_code.return_value = 0
            mock_manager.get_output.return_value = "test output"
            mock_manager._is_screen_session_running.return_value = True
            mock_get_manager.return_value = mock_manager
            
            for tool_func, args in mcp_tools:
                def test_tool():
                    return tool_func(*args)
                
                stats = measure_performance(test_tool, iterations=100)
                
                # All MCP tools should meet response time threshold
                assert stats['mean'] < performance_threshold['mcp_tool_response'], \
                    f"MCP tool {tool_func.__name__} too slow: {stats['mean']:.6f}s"
                
                assert stats['p95'] < performance_threshold['mcp_tool_response'] * 2, \
                    f"MCP tool {tool_func.__name__} 95th percentile too slow: {stats['p95']:.6f}s"
    
    def test_mcp_tools_concurrent_performance(self):
        """Test MCP tools performance under concurrent load."""
        import threading
        import queue
        
        results_queue = queue.Queue()
        thread_count = 10
        operations_per_thread = 20
        
        with patch('screen_manager.mcp_server.get_session_manager') as mock_get_manager:
            mock_manager = Mock()
            mock_manager.get_session_status.return_value = {'status': 'running'}
            mock_get_manager.return_value = mock_manager
            
            def worker():
                """Worker function for concurrent testing."""
                thread_results = []
                
                for _ in range(operations_per_thread):
                    start_time = time.time()
                    get_session_status("concurrent-test")
                    end_time = time.time()
                    thread_results.append(end_time - start_time)
                
                results_queue.put(thread_results)
            
            # Start concurrent workers
            threads = []
            start_time = time.time()
            
            for _ in range(thread_count):
                thread = threading.Thread(target=worker)
                threads.append(thread)
                thread.start()
            
            # Wait for completion
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # Collect all timing results
            all_times = []
            while not results_queue.empty():
                thread_times = results_queue.get()
                all_times.extend(thread_times)
            
            # Analyze concurrent performance
            total_operations = thread_count * operations_per_thread
            avg_response_time = statistics.mean(all_times)
            throughput = total_operations / total_time
            
            assert avg_response_time < 0.1, f"Average response time under load: {avg_response_time:.6f}s"
            assert throughput > 50, f"Throughput too low: {throughput:.1f} ops/sec"
    
    def test_wait_for_completion_timeout_performance(self):
        """Test wait_for_completion timeout performance."""
        with patch('screen_manager.mcp_server.get_session_manager') as mock_get_manager:
            mock_manager = Mock()
            
            # Mock session that never completes
            mock_manager.get_session_status.return_value = {
                'status': 'running',
                'exit_code': None
            }
            
            mock_get_manager.return_value = mock_manager
            
            # Test short timeout performance
            start_time = time.time()
            result = wait_for_completion("never-completes", timeout=1)
            duration = time.time() - start_time
            
            # Should timeout close to requested time
            assert 0.9 <= duration <= 1.5, f"Timeout took {duration:.3f}s, expected ~1.0s"
            assert result['success'] is False
            assert result['status'] == 'timeout'


@pytest.mark.performance
class TestCLIPerformance:
    """Performance tests for CLI interface."""
    
    def test_argument_parsing_performance(self):
        """Test CLI argument parsing performance."""
        test_commands = [
            ['serve'],
            ['serve', '--transport', 'http', '--port', '9000'],
            ['debug', '--name', 'test', '--command', 'python script.py', '--create'],
            ['debug', '--list'],
            ['info']
        ]
        
        for args in test_commands:
            def parse_args():
                with patch('screen_manager.cli.serve_command', return_value=0), \
                     patch('screen_manager.cli.debug_command', return_value=0), \
                     patch('screen_manager.cli.info_command', return_value=0):
                    
                    main(args)
            
            stats = measure_performance(parse_args, iterations=100)
            
            # Argument parsing should be very fast
            assert stats['mean'] < 0.01, f"Parsing {args} too slow: {stats['mean']:.6f}s"
            assert stats['max'] < 0.05, f"Max parsing time for {args} too slow: {stats['max']:.6f}s"
    
    def test_cli_info_command_performance(self):
        """Test CLI info command performance."""
        with patch('subprocess.run') as mock_subprocess, \
             patch('screen_manager.cli.get_agent_id', return_value='perf-agent'), \
             patch('os.getcwd', return_value='/test'), \
             patch('builtins.print'):
            
            # Mock fast subprocess responses
            mock_result = Mock()
            mock_result.stdout = "Screen version 4.09.00"
            mock_result.returncode = 0
            mock_subprocess.return_value = mock_result
            
            def run_info():
                return main(['info'])
            
            stats = measure_performance(run_info, iterations=50)
            
            # Info command should be fast
            assert stats['mean'] < 0.5, f"Info command too slow: {stats['mean']:.6f}s"
            assert stats['p95'] < 1.0, f"Info command 95th percentile too slow: {stats['p95']:.6f}s"
    
    def test_cli_debug_workflow_performance(self):
        """Test CLI debug workflow performance."""
        with patch('screen_manager.cli.ScreenSessionManager') as mock_manager_class, \
             patch('builtins.print'):
            
            # Setup fast mock manager
            mock_manager = Mock()
            mock_manager.agent_id = "cli-perf-agent"
            mock_manager.create_session.return_value = {'success': True}
            mock_manager.list_sessions.return_value = []
            mock_manager_class.return_value = mock_manager
            
            def run_debug_list():
                return main(['debug', '--list'])
            
            stats = measure_performance(run_debug_list, iterations=100)
            
            # Debug operations should be fast
            assert stats['mean'] < 0.1, f"Debug list too slow: {stats['mean']:.6f}s"
            assert stats['max'] < 0.5, f"Max debug list time too slow: {stats['max']:.6f}s"


@pytest.mark.performance
@pytest.mark.integration
class TestIntegratedPerformance:
    """Performance tests for integrated workflows."""
    
    def test_end_to_end_session_workflow_performance(self):
        """Test complete session workflow performance."""
        with create_mock_screen_environment() as mock_screen:
            workflow_steps = []
            
            # Step 1: Create session
            start_time = time.time()
            create_result = create_debug_session(
                "perf-workflow",
                "python workflow_test.py",
                agent_id="perf-agent"
            )
            workflow_steps.append(('create', time.time() - start_time))
            assert create_result['success']
            
            # Step 2: Check status
            start_time = time.time()
            status_result = get_session_status("perf-workflow")
            workflow_steps.append(('status', time.time() - start_time))
            
            # Step 3: Send command
            start_time = time.time()
            send_result = send_command("perf-workflow", "print('performance test')")
            workflow_steps.append(('command', time.time() - start_time))
            
            # Step 4: Get output
            start_time = time.time()
            output_result = get_session_output("perf-workflow")
            workflow_steps.append(('output', time.time() - start_time))
            
            # Analyze workflow performance
            total_time = sum(duration for _, duration in workflow_steps)
            max_step_time = max(duration for _, duration in workflow_steps)
            
            assert total_time < 2.0, f"Complete workflow too slow: {total_time:.3f}s"
            assert max_step_time < 0.5, f"Slowest step too slow: {max_step_time:.3f}s"
            
            # Check individual step performance
            step_thresholds = {
                'create': 1.0,   # Session creation can be slower
                'status': 0.1,   # Status should be fast
                'command': 0.1,  # Commands should be fast
                'output': 0.1    # Output should be fast
            }
            
            for step_name, duration in workflow_steps:
                threshold = step_thresholds[step_name]
                assert duration < threshold, \
                    f"Step {step_name} too slow: {duration:.6f}s (threshold: {threshold}s)"
    
    def test_multi_agent_performance_scenario(self):
        """Test performance with multiple agents operating simultaneously."""
        agent_count = 5
        operations_per_agent = 10
        
        with create_mock_screen_environment():
            start_time = time.time()
            
            # Simulate multiple agents creating sessions
            for agent_id in range(agent_count):
                for operation_id in range(operations_per_agent):
                    session_name = f"agent{agent_id}-op{operation_id}"
                    
                    result = create_debug_session(
                        session_name,
                        f"python agent_{agent_id}_task_{operation_id}.py",
                        agent_id=f"perf-agent-{agent_id}"
                    )
                    
                    assert result['success']
            
            total_time = time.time() - start_time
            total_operations = agent_count * operations_per_agent
            avg_time_per_operation = total_time / total_operations
            
            # Performance requirements for multi-agent scenario
            assert total_time < 20.0, f"Multi-agent scenario too slow: {total_time:.3f}s"
            assert avg_time_per_operation < 0.4, \
                f"Average operation time too slow: {avg_time_per_operation:.6f}s"
    
    def test_memory_usage_performance(self):
        """Test memory usage remains reasonable during operation."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        with create_mock_screen_environment() as mock_screen:
            # Create many sessions to test memory usage
            session_count = 100
            
            for i in range(session_count):
                mock_screen.create_session(f"memory-test-{i}", f"python task_{i}.py")
                
                # Periodically check memory usage
                if i % 20 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024  # MB
                    memory_increase = current_memory - initial_memory
                    
                    # Memory usage should not grow excessively
                    assert memory_increase < 50, \
                        f"Memory usage too high after {i} sessions: {memory_increase:.1f}MB increase"
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_memory_increase = final_memory - initial_memory
            
            # Total memory increase should be reasonable
            assert total_memory_increase < 100, \
                f"Total memory increase too high: {total_memory_increase:.1f}MB"


@pytest.mark.performance
def test_performance_regression_baseline():
    """Establish baseline performance measurements for regression testing."""
    baseline_measurements = {}
    
    # Agent ID detection baseline
    with patch.dict('os.environ', {'CLAUDE_AGENT_ID': 'baseline-test'}):
        stats = measure_performance(get_agent_id, iterations=1000)
        baseline_measurements['get_agent_id'] = stats
    
    # Condition evaluation baseline
    stats = measure_performance(lambda: check_condition(True), iterations=1000)
    baseline_measurements['check_condition_bool'] = stats
    
    # Session status check baseline (mocked)
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = ""
        
        manager = ScreenSessionManager(agent_id="baseline-agent")
        with patch.object(manager, '_is_screen_session_running', return_value=True), \
             patch.object(manager, '_get_exit_code', return_value=None):
            
            stats = measure_performance(
                lambda: manager.get_session_status("baseline-test"), 
                iterations=100
            )
            baseline_measurements['session_status'] = stats
    
    # Print baseline measurements for regression tracking
    print("\nPerformance Baseline Measurements:")
    print("=" * 50)
    
    for operation, stats in baseline_measurements.items():
        print(f"{operation}:")
        print(f"  Mean: {stats['mean']:.6f}s")
        print(f"  P95:  {stats['p95']:.6f}s")
        print(f"  Max:  {stats['max']:.6f}s")
        print()
    
    # Assert baseline performance is reasonable
    assert baseline_measurements['get_agent_id']['mean'] < 0.001
    assert baseline_measurements['check_condition_bool']['mean'] < 0.001
    assert baseline_measurements['session_status']['mean'] < 0.1


if __name__ == "__main__":
    print("Running performance tests...")
    pytest.main([__file__, "-v", "-m", "performance"])