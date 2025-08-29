#!/usr/bin/env python3
"""
Test runner script for screen-manager.

Provides comprehensive test execution with coverage reporting, performance 
benchmarking, and integration with the project's testing philosophy.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run command and return result."""
    print(f"Running: {' '.join(cmd)}")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)


def run_unit_tests(coverage: bool = True, verbose: bool = True) -> int:
    """Run unit tests with optional coverage."""
    print("🧪 Running Unit Tests")
    print("=" * 50)
    
    cmd = ["python", "-m", "pytest", "tests/unit/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend([
            "--cov=src/screen_manager",
            "--cov-report=term-missing",
            "--cov-report=html:tests/reports/htmlcov",
            "--cov-fail-under=95"
        ])
    
    result = run_command(cmd)
    
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode


def run_integration_tests(verbose: bool = True) -> int:
    """Run integration tests."""
    print("🔗 Running Integration Tests")
    print("=" * 50)
    
    cmd = ["python", "-m", "pytest", "tests/integration/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    result = run_command(cmd)
    
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode


def run_performance_tests(verbose: bool = True) -> int:
    """Run performance tests."""
    print("⚡ Running Performance Tests")
    print("=" * 50)
    
    cmd = ["python", "-m", "pytest", "tests/test_performance.py", "-m", "performance"]
    
    if verbose:
        cmd.extend(["-v", "-s"])  # Show performance output
    
    result = run_command(cmd)
    
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode


def run_linting() -> int:
    """Run code linting with ruff."""
    print("🔍 Running Code Linting")
    print("=" * 50)
    
    # Check formatting
    format_result = run_command(["python", "-m", "ruff", "format", "--check", "src/", "tests/"])
    
    if format_result.returncode != 0:
        print("❌ Code formatting issues found:")
        print(format_result.stdout)
        return format_result.returncode
    
    # Check linting
    lint_result = run_command(["python", "-m", "ruff", "check", "src/", "tests/"])
    
    if lint_result.returncode != 0:
        print("❌ Linting issues found:")
        print(lint_result.stdout)
        return lint_result.returncode
    
    print("✅ All linting checks passed")
    return 0


def run_type_checking() -> int:
    """Run type checking with mypy."""
    print("🔬 Running Type Checking")
    print("=" * 50)
    
    result = run_command(["python", "-m", "mypy", "src/screen_manager/"])
    
    if result.returncode != 0:
        print("❌ Type checking issues found:")
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return result.returncode
    
    print("✅ Type checking passed")
    return 0


def run_smoke_tests() -> int:
    """Run quick smoke tests for CI."""
    print("💨 Running Smoke Tests")
    print("=" * 50)
    
    cmd = [
        "python", "-m", "pytest", 
        "tests/unit/test_cipdb.py::TestGetAgentId::test_get_agent_id_from_claude_agent_id",
        "tests/unit/test_screen_manager.py::TestScreenSessionManagerInit::test_init_default",
        "tests/unit/test_mcp_server.py::TestGetSessionManager::test_get_session_manager_singleton",
        "tests/unit/test_cli.py::TestMainFunction::test_main_no_command",
        "-v", "--tb=short"
    ]
    
    result = run_command(cmd)
    
    print("STDOUT:", result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)
    
    return result.returncode


def create_test_reports_dir():
    """Create test reports directory."""
    reports_dir = Path("tests/reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


def generate_coverage_badge(coverage_file: Path) -> None:
    """Generate coverage badge from coverage data."""
    try:
        import json
        
        if coverage_file.exists():
            with open(coverage_file) as f:
                coverage_data = json.load(f)
            
            total_coverage = coverage_data.get('totals', {}).get('percent_covered', 0)
            
            print(f"📊 Total Coverage: {total_coverage:.1f}%")
            
            # Create simple badge info
            badge_info = {
                'coverage': total_coverage,
                'color': 'green' if total_coverage >= 95 else 'yellow' if total_coverage >= 80 else 'red',
                'status': 'passing' if total_coverage >= 95 else 'needs improvement'
            }
            
            badge_file = Path("tests/reports/coverage_badge.json")
            with open(badge_file, 'w') as f:
                json.dump(badge_info, f, indent=2)
            
            print(f"📋 Coverage badge info saved to {badge_file}")
    
    except ImportError:
        print("⚠️  Could not generate coverage badge (missing json module)")


def run_full_test_suite(args) -> int:
    """Run complete test suite with all quality gates."""
    print("🚀 Running Full Test Suite")
    print("=" * 70)
    
    # Create reports directory
    create_test_reports_dir()
    
    results = {}
    
    # 1. Linting
    if not args.skip_lint:
        results['linting'] = run_linting()
    
    # 2. Type checking  
    if not args.skip_types:
        results['type_checking'] = run_type_checking()
    
    # 3. Unit tests with coverage
    if not args.skip_unit:
        results['unit_tests'] = run_unit_tests(coverage=not args.skip_coverage, verbose=args.verbose)
    
    # 4. Integration tests
    if not args.skip_integration:
        results['integration_tests'] = run_integration_tests(verbose=args.verbose)
    
    # 5. Performance tests
    if not args.skip_performance:
        results['performance_tests'] = run_performance_tests(verbose=args.verbose)
    
    # Generate coverage badge
    if not args.skip_coverage:
        coverage_json = Path("tests/reports/coverage.json")
        generate_coverage_badge(coverage_json)
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUITE SUMMARY")
    print("=" * 70)
    
    all_passed = True
    for test_type, return_code in results.items():
        status = "✅ PASSED" if return_code == 0 else "❌ FAILED"
        print(f"{test_type.replace('_', ' ').title():<20} {status}")
        if return_code != 0:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All quality gates passed! Ready for commit.")
        return 0
    else:
        print("\n💥 Some quality gates failed. Please fix issues before committing.")
        return 1


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description="Screen Session Manager Test Runner")
    
    # Test selection
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument("--integration", action="store_true", help="Run only integration tests")
    parser.add_argument("--performance", action="store_true", help="Run only performance tests")
    parser.add_argument("--smoke", action="store_true", help="Run only smoke tests")
    
    # Quality gates
    parser.add_argument("--skip-lint", action="store_true", help="Skip linting")
    parser.add_argument("--skip-types", action="store_true", help="Skip type checking")
    parser.add_argument("--skip-coverage", action="store_true", help="Skip coverage reporting")
    parser.add_argument("--skip-unit", action="store_true", help="Skip unit tests")
    parser.add_argument("--skip-integration", action="store_true", help="Skip integration tests")
    parser.add_argument("--skip-performance", action="store_true", help="Skip performance tests")
    
    # Output control
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output")
    
    args = parser.parse_args()
    
    # Adjust working directory to project root
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)
    
    # Run specific test types if requested
    if args.smoke:
        return run_smoke_tests()
    elif args.unit:
        return run_unit_tests(coverage=not args.skip_coverage, verbose=args.verbose)
    elif args.integration:
        return run_integration_tests(verbose=args.verbose)
    elif args.performance:
        return run_performance_tests(verbose=args.verbose)
    else:
        # Run full test suite
        return run_full_test_suite(args)


if __name__ == "__main__":
    sys.exit(main())