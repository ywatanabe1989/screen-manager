#!/usr/bin/env python3
"""Test script for the send_command_from_file functionality"""

import sys
import os
import time
sys.path.insert(0, 'src')

from screen_manager.ScreenSessionManager import ScreenSessionManager

def test_send_command_from_file():
    """Test the send_command_from_file method"""
    print("Testing send_command_from_file functionality...")
    
    # Create manager and test session
    manager = ScreenSessionManager(verbose=True)
    
    # Create test session
    print("\n1. Creating test session...")
    create_result = manager.create_session("test-file-commands", verbose=True)
    print(f"Create result: {create_result}")
    
    if not create_result.get("success"):
        print("Failed to create session, aborting test")
        return
    
    try:
        # Test 1: Execute shell script
        print("\n2. Testing 'execute' mode with shell script...")
        result1 = manager.send_command_from_file(
            "test-file-commands", 
            "test_commands.sh", 
            mode="execute",
            verbose=True
        )
        print(f"Shell script result: {result1}")
        
        # Wait a moment and capture output
        time.sleep(2)
        output1 = manager.capture("test-file-commands", n_lines=10)
        print(f"Shell script output:\n{output1}")
        
        # Test 2: Execute Python script  
        print("\n3. Testing 'execute' mode with Python script...")
        result2 = manager.send_command_from_file(
            "test-file-commands",
            "test_python.py", 
            mode="execute",
            verbose=True
        )
        print(f"Python script result: {result2}")
        
        # Wait and capture
        time.sleep(2)
        output2 = manager.capture("test-file-commands", n_lines=10)
        print(f"Python script output:\n{output2}")
        
        # Test 3: Send lines mode
        print("\n4. Testing 'lines' mode...")
        result3 = manager.send_command_from_file(
            "test-file-commands",
            "test_lines.txt",
            mode="lines", 
            delay_between_lines=0.5,
            verbose=True
        )
        print(f"Lines mode result: {result3}")
        
        # Wait and capture
        time.sleep(3)
        output3 = manager.capture("test-file-commands", n_lines=15)
        print(f"Lines mode output:\n{output3}")
        
        # Test 4: Test file not found
        print("\n5. Testing error handling (file not found)...")
        result4 = manager.send_command_from_file(
            "test-file-commands",
            "nonexistent_file.txt",
            verbose=True
        )
        print(f"File not found result: {result4}")
        
        # Test 5: Test session not found
        print("\n6. Testing error handling (session not found)...")
        result5 = manager.send_command_from_file(
            "nonexistent-session",
            "test_commands.sh",
            verbose=True
        )
        print(f"Session not found result: {result5}")
        
    finally:
        # Clean up
        print("\n7. Cleaning up...")
        cleanup_result = manager.cleanup_session("test-file-commands")
        print(f"Cleanup result: {cleanup_result}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_send_command_from_file()