#!/usr/bin/env python3
"""Test script for the new list_sessions and attach_session methods"""

import sys
import os
sys.path.insert(0, 'src')

from screen_manager.ScreenSessionManager import ScreenSessionManager

def test_new_methods():
    """Test the new list_sessions and attach_session methods"""
    print("Testing new ScreenSessionManager methods...")
    
    # Create manager
    manager = ScreenSessionManager(verbose=True)
    
    # Test list_sessions (all sessions)
    print("\n1. Testing list_sessions(all_sessions=True)...")
    all_sessions = manager.list_sessions(all_sessions=True)
    print(f"All sessions result: {all_sessions}")
    
    # Test list_sessions (managed only)
    print("\n2. Testing list_sessions(all_sessions=False)...")
    managed_sessions = manager.list_sessions(all_sessions=False)
    print(f"Managed sessions result: {managed_sessions}")
    
    # Create a test session first
    print("\n3. Creating test session...")
    create_result = manager.create_session("test-new-methods", verbose=True)
    print(f"Create result: {create_result}")
    
    if create_result.get("success"):
        # Test list_sessions again after creating session
        print("\n4. Testing list_sessions after creating session...")
        managed_sessions = manager.list_sessions(all_sessions=False)
        print(f"Managed sessions after creation: {managed_sessions}")
        
        # Test attach_session
        print("\n5. Testing attach_session...")
        attach_result = manager.attach_session("test-new-methods", verbose=True)
        print(f"Attach result: {attach_result}")
        
        # Clean up
        print("\n6. Cleaning up...")
        cleanup_result = manager.cleanup_session("test-new-methods")
        print(f"Cleanup result: {cleanup_result}")
    
    # Test create_or_attach_session
    print("\n7. Testing create_or_attach_session (new session)...")
    create_or_attach_result = manager.create_or_attach_session("test-create-or-attach", verbose=True)
    print(f"Create or attach result (new): {create_or_attach_result}")
    
    if create_or_attach_result.get("success"):
        print("\n8. Testing create_or_attach_session (existing session)...")
        create_or_attach_existing = manager.create_or_attach_session("test-create-or-attach", verbose=True)
        print(f"Create or attach result (existing): {create_or_attach_existing}")
        
        # Clean up
        print("\n9. Cleaning up create_or_attach test session...")
        cleanup_result2 = manager.cleanup_session("test-create-or-attach")
        print(f"Cleanup result: {cleanup_result2}")
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    test_new_methods()