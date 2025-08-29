#!/usr/bin/env python3
"""Test script for the MCP server using the underlying ScreenSessionManager directly"""

import sys
import os
sys.path.insert(0, 'src')

from screen_manager.ScreenSessionManager import ScreenSessionManager

def test_screen_manager():
    """Test the underlying ScreenSessionManager that the MCP server uses"""
    print("Testing ScreenSessionManager (used by MCP server)...")
    
    # Create manager
    manager = ScreenSessionManager(verbose=True)
    
    # Test creating a session
    print("\n1. Testing create_session...")
    result = manager.create_session("test-session", verbose=True)
    print(f"Create session result: {result}")
    
    # Test sending a command
    if result.get("success"):
        print("\n2. Testing send_command...")
        cmd_result = manager.send_command("test-session", "echo 'Hello from MCP test'", verbose=True)
        print(f"Command result: {cmd_result}")
        
        # Test capturing output
        print("\n3. Testing capture...")
        import time
        time.sleep(1)  # Wait a moment for command to execute
        output = manager.capture("test-session", n_lines=5)
        print(f"Captured output:\n{output}")
        
        # Clean up
        print("\n4. Testing cleanup...")
        cleanup_result = manager.cleanup_session("test-session")
        print(f"Cleanup result: {cleanup_result}")
    
    print("\nAll tests completed!")

def test_mcp_server_import():
    """Test that the MCP server can be imported and initialized"""
    print("Testing MCP server import...")
    try:
        from screen_manager.mcp_server import mcp
        print(f"MCP server imported successfully: {mcp}")
        
        # Get the tools list - try different attributes for FastMCP v2
        try:
            if hasattr(mcp, 'tools'):
                tools = list(mcp.tools.keys())
            elif hasattr(mcp, '_tools'):
                tools = list(mcp._tools.keys())
            else:
                tools = "Unable to access tools list"
            print(f"Available tools: {tools}")
        except Exception as e:
            print(f"Could not list tools: {e}")
        
        return True
    except Exception as e:
        print(f"MCP server import failed: {e}")
        return False

if __name__ == "__main__":
    # Test MCP server import first
    if test_mcp_server_import():
        print("\n" + "="*50)
        # Test underlying functionality
        test_screen_manager()