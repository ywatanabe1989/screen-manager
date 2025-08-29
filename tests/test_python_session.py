#!/usr/bin/env python3
"""Comprehensive test of Python screen session management via MCP."""

import time
import json

def test_python_session():
    """Test Python-specific screen session features."""
    
    print("=" * 60)
    print("Testing Python Screen Session Manager")
    print("=" * 60)
    
    # Test 1: Basic Python interpreter
    print("\n1. Testing basic Python interpreter...")
    commands = [
        "python3",
        "print('Hello from Python')",
        "x = 42",
        "print(f'The answer is {x}')",
        "import sys",
        "print(sys.version)",
        "exit()"
    ]
    
    # Test 2: IPython session
    print("\n2. Testing IPython session...")
    ipython_commands = [
        "ipython",
        "import numpy as np",
        "arr = np.array([1, 2, 3, 4, 5])",
        "print(arr.mean())",
        "%timeit sum(range(100))",
        "exit"
    ]
    
    # Test 3: Debugging with ipdb
    print("\n3. Testing ipdb debugging...")
    debug_script = '''
def calculate(a, b):
    import ipdb; ipdb.set_trace()
    result = a + b
    return result

result = calculate(10, 20)
print(f"Result: {result}")
'''
    
    # Test 4: Error handling
    print("\n4. Testing error handling...")
    error_commands = [
        "python3",
        "1/0",  # ZeroDivisionError
        "undefined_variable",  # NameError
        "import nonexistent_module",  # ModuleNotFoundError
        "exit()"
    ]
    
    # Test 5: Long-running process
    print("\n5. Testing long-running process...")
    long_running = '''
import time
for i in range(5):
    print(f"Processing step {i+1}/5...")
    time.sleep(1)
print("Done!")
'''
    
    return {
        "basic_python": commands,
        "ipython": ipython_commands,
        "debug_script": debug_script,
        "error_handling": error_commands,
        "long_running": long_running
    }

if __name__ == "__main__":
    tests = test_python_session()
    print("\nTest scenarios prepared:")
    for name, content in tests.items():
        print(f"  - {name}")
    
    print("\nTo run these tests via MCP:")
    print("1. Create a Python session")
    print("2. Send the commands from each test scenario")
    print("3. Capture and verify the output")
    print("4. Check state detection (normal/ipython/ipdb)")