#!/usr/bin/env python3
"""Test state detection for Python screen sessions."""

import json
import time

def test_state_transitions():
    """Test different Python interpreter states."""
    
    test_scenarios = [
        {
            "name": "Normal Shell",
            "commands": ["echo 'In normal shell'"],
            "expected_state": "shell",
            "expected_prompt": "$"
        },
        {
            "name": "Python REPL",
            "commands": ["python3", "print('In Python')"],
            "expected_state": "python",
            "expected_prompt": ">>>"
        },
        {
            "name": "IPython REPL",
            "commands": ["exit()", "ipython", "print('In IPython')"],
            "expected_state": "ipython",
            "expected_prompt": "In ["
        },
        {
            "name": "IPDB Debugger",
            "commands": ["exit", "python3 -c \"import ipdb; ipdb.set_trace()\""],
            "expected_state": "ipdb",
            "expected_prompt": "ipdb>"
        },
        {
            "name": "Back to Shell",
            "commands": ["c", "echo 'Back to shell'"],
            "expected_state": "shell",
            "expected_prompt": "$"
        }
    ]
    
    return test_scenarios

def analyze_output_for_state(output):
    """Analyze captured output to detect current state."""
    
    # Look for prompts in reverse order (most recent first)
    lines = output.strip().split('\n')
    
    for line in reversed(lines):
        line = line.strip()
        
        # Check for ipdb prompt
        if 'ipdb>' in line:
            return "ipdb", line
        
        # Check for IPython prompt
        if line.startswith('In [') and ']:' in line:
            return "ipython", line
        
        # Check for Python prompt
        if line.startswith('>>>') or line.startswith('...'):
            return "python", line
        
        # Check for shell prompt
        if '$' in line and not line.startswith('#'):
            return "shell", line
    
    return "unknown", ""

if __name__ == "__main__":
    scenarios = test_state_transitions()
    
    print("State Detection Test Scenarios:")
    print("=" * 50)
    
    for scenario in scenarios:
        print(f"\n{scenario['name']}:")
        print(f"  Commands: {scenario['commands']}")
        print(f"  Expected State: {scenario['expected_state']}")
        print(f"  Expected Prompt: {scenario['expected_prompt']}")
    
    print("\n" + "=" * 50)
    print("To run these tests:")
    print("1. Execute commands in sequence")
    print("2. Capture output after each command set")
    print("3. Use analyze_output_for_state() to detect state")
    print("4. Verify state matches expected")