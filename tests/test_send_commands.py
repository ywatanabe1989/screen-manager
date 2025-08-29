#!/usr/bin/env python3
"""Test script for the send_commands functionality"""

import sys
import os
import time
sys.path.insert(0, 'src')

from screen_manager.ScreenSessionManager import ScreenSessionManager

def test_send_commands():
    """Test the send_commands method"""
    print("Testing send_commands functionality...")
    
    # Create manager and test session
    manager = ScreenSessionManager(verbose=True)
    
    # Create test session
    print("\n1. Creating test session...")
    create_result = manager.create_session("test-commands-list", verbose=True)
    print(f"Create result: {create_result}")
    
    if not create_result.get("success"):
        print("Failed to create session, aborting test")
        return
    
    try:
        # Test 1: Send basic commands successfully
        print("\n2. Testing basic commands (all successful)...")
        basic_commands = [
            "echo 'Command 1: Hello World'",
            "echo 'Command 2: Current directory'",
            "pwd",
            "echo 'Command 3: Date and time'",
            "date"
        ]
        
        result1 = manager.send_commands(
            "test-commands-list",
            basic_commands,
            delay_between_commands=0.3,
            verbose=True
        )
        print(f"Basic commands result: {result1}")
        
        # Wait and capture output
        time.sleep(2)
        output1 = manager.capture("test-commands-list", n_lines=15)
        print(f"Basic commands output:\n{output1}")
        
        # Test 2: Mixed successful and failing commands with stop_on_failure=True
        print("\n3. Testing mixed commands with stop_on_failure=True...")
        mixed_commands = [
            "echo 'This will succeed'",
            "nonexistent_command_that_will_fail",  # This should fail
            "echo 'This should not execute'"       # This should not be reached
        ]
        
        result2 = manager.send_commands(
            "test-commands-list",
            mixed_commands,
            stop_on_failure=True,
            verbose=True
        )
        print(f"Mixed commands (stop on failure) result: {result2}")
        
        # Test 3: Mixed commands with stop_on_failure=False
        print("\n4. Testing mixed commands with stop_on_failure=False...")
        mixed_commands_2 = [
            "echo 'First command'",
            "nonexistent_command_again",  # This will fail but we'll continue
            "echo 'Third command - should execute'",
            "invalid_cmd_2",              # Another failure
            "echo 'Final command - should execute'"
        ]
        
        result3 = manager.send_commands(
            "test-commands-list",
            mixed_commands_2,
            stop_on_failure=False,
            delay_between_commands=0.2,
            verbose=True
        )
        print(f"Mixed commands (continue on failure) result: {result3}")
        
        # Wait and capture output
        time.sleep(2)
        output2 = manager.capture("test-commands-list", n_lines=20)
        print(f"Mixed commands output:\n{output2}")
        
        # Test 4: Empty commands list
        print("\n5. Testing empty commands list...")
        result4 = manager.send_commands(
            "test-commands-list",
            [],
            verbose=True
        )
        print(f"Empty commands result: {result4}")
        
        # Test 5: Commands with empty strings and whitespace
        print("\n6. Testing commands with empty strings...")
        whitespace_commands = [
            "echo 'Before empty'",
            "",                    # Empty command - should be skipped
            "   ",                 # Whitespace only - should be skipped
            "echo 'After empty'"
        ]
        
        result5 = manager.send_commands(
            "test-commands-list",
            whitespace_commands,
            verbose=True
        )
        print(f"Whitespace commands result: {result5}")
        
        # Test 6: No delay between commands (fast execution)
        print("\n7. Testing fast execution (no delay)...")
        fast_commands = [
            "echo 'Fast 1'",
            "echo 'Fast 2'", 
            "echo 'Fast 3'"
        ]
        
        result6 = manager.send_commands(
            "test-commands-list",
            fast_commands,
            delay_between_commands=0,
            verbose=True
        )
        print(f"Fast commands result: {result6}")
        
    finally:
        # Clean up
        print("\n8. Cleaning up...")
        cleanup_result = manager.cleanup_session("test-commands-list")
        print(f"Cleanup result: {cleanup_result}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_send_commands()