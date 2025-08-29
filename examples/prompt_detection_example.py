#!/usr/bin/env python3
"""Example of detecting command completion using prompt detection.

Note: This is a heuristic approach and may not work with customized prompts.
"""

import time
from screen_manager import ScreenSessionManager
from screen_manager.prompt_detection import detect_prompt_state, is_ready_for_input


def wait_for_command_completion(manager, session_name, max_wait=10, check_interval=0.5):
    """Wait for a command to complete by checking for prompts.
    
    Args:
        manager: ScreenSessionManager instance
        session_name: Name of the session
        max_wait: Maximum seconds to wait
        check_interval: Seconds between checks
        
    Returns:
        Tuple of (completed, output, detected_state)
    """
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        output = manager.capture(session_name, n_lines=-1)
        state, last_line = detect_prompt_state(output)
        
        if is_ready_for_input(output):
            return True, output, state
            
        time.sleep(check_interval)
    
    # Timeout - return what we have
    output = manager.capture(session_name, n_lines=-1)
    state, _ = detect_prompt_state(output)
    return False, output, state


def main():
    """Demonstrate prompt detection with various commands."""
    
    manager = ScreenSessionManager()
    session_name = "prompt-test"
    
    # Create session
    result = manager.create_session(session_name)
    if not result['success']:
        print(f"Failed to create session: {result['error']}")
        return
        
    full_session_name = result['session_name']
    print(f"Created session: {full_session_name}")
    
    # Test cases
    test_commands = [
        ("echo 'Quick command'", "shell", 2),
        ("python3 -c 'print(42)'", "shell", 3),
        ("python3", "python", 3),
        ("print('Hello from Python')", "python", 2),
        ("exit()", "shell", 2),
    ]
    
    for command, expected_state, timeout in test_commands:
        print(f"\n{'='*50}")
        print(f"Sending: {command}")
        
        # Send command
        manager.send_command(full_session_name, command)
        
        # Wait for completion
        completed, output, state = wait_for_command_completion(
            manager, full_session_name, max_wait=timeout
        )
        
        print(f"Completed: {completed}")
        print(f"Detected state: {state} (expected: {expected_state})")
        
        if state != expected_state and expected_state != "any":
            print("WARNING: State detection may have failed!")
            
        # Show last few lines of output
        lines = output.strip().split('\n')
        print("Last 3 lines of output:")
        for line in lines[-3:]:
            print(f"  > {line}")
    
    # Cleanup
    manager.cleanup(full_session_name)
    print(f"\nCleaned up session: {full_session_name}")


if __name__ == "__main__":
    main()