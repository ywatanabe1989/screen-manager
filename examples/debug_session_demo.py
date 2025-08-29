#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-29 18:51:22 (ywatanabe)"
# File: /home/ywatanabe/proj/screen-manager/examples/debug_session_demo.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./examples/debug_session_demo.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

"""
Demo: PythonScreenSessionManager IPDB/CIPDB Integration

This example demonstrates how to use PythonScreenSessionManager to:
1. Execute Python scripts with debugging
2. Detect and handle IPDB/CIPDB debugging sessions
3. Interact with debugger sessions programmatically
4. Handle exceptions and provide debugging context
"""

from pathlib import Path

from screen_manager import PythonScreenSessionManager


def demo_debugging_workflow():
    """Demonstrate a complete debugging workflow."""

    print("=" * 60)
    print("🐍 PythonScreenSessionManager IPDB/CIPDB Demo")
    print("=" * 60)

    # Create manager with analysis enabled
    manager = PythonScreenSessionManager(
        session_name="debug-demo",
        enable_analysis=True,
        deep_analysis=True,
        verbose=True,
    )

    try:
        # Step 1: Create a Python session
        print("\n📝 Step 1: Creating Python session...")
        session_result = manager.create_session(
            "debug-session",
            use_ipython=False,  # Use regular Python for debugging
            verbose=True,
        )

        if not session_result["success"]:
            print(f"❌ Failed to create session: {session_result}")
            return

        print(f"✅ Session created: {session_result['session_name']}")
        print(f"🔍 Python state: {session_result['python_state']}")

        # Step 2: Execute the script with CIPDB
        print("\n📝 Step 2: Executing script with CIPDB...")
        script_path = str(Path(__file__).parent / "script_with_cipdb.py")

        exec_result = manager.send_and_wait(
            "debug-session",
            f"exec(open('{script_path}').read())",
            timeout=10,
            verbose=True,
        )

        print(f"🔍 Command execution success: {exec_result['success']}")
        print(f"🔍 Exit code: {exec_result.get('exit_code', 'N/A')}")

        # Step 3: Analyze the output for debugging state
        print("\n📝 Step 3: Analyzing session state...")
        status = manager.get_session_status("debug-session", verbose=True)

        print(
            f"🔍 Current Python state: {status.get('python_state', 'unknown')}"
        )
        print(
            f"🔍 Interpreter type: {status.get('interpreter_type', 'unknown')}"
        )

        # Step 4: Check for exceptions
        print("\n📝 Step 4: Checking for exceptions...")
        if exec_result.get("exceptions_found"):
            print("🚨 Exceptions detected!")

            # Handle the exception with our manager
            exception_result = manager.handle_python_exception(
                "debug-session", auto_debug=True
            )

            if exception_result["success"]:
                print("✅ Exception handling result:")
                for suggestion in exception_result.get(
                    "debug_suggestions", []
                ):
                    print(f"  💡 {suggestion}")

        # Step 5: Detect current Python state (might be in IPDB)
        print("\n📝 Step 5: Deep state detection...")
        state_result = manager.detect_python_state(
            "debug-session", deep_scan=True
        )

        if state_result["success"]:
            python_state = state_result["python_state"]
            print(
                f"🔍 Detected environment: {python_state['environment_type']}"
            )
            print(f"🔍 Confidence: {python_state.get('confidence', 0):.2f}")

            # If we're in a debugging state, show debugging commands
            if python_state["environment_type"] in ["ipdb", "ipython"]:
                print("\n🛠️  Debugging commands you can use:")
                print(
                    "  • manager.send_command('debug-session', 'l') - List current code"
                )
                print(
                    "  • manager.send_command('debug-session', 'p variable_name') - Print variable"
                )
                print(
                    "  • manager.send_command('debug-session', 'n') - Next line"
                )
                print(
                    "  • manager.send_command('debug-session', 'c') - Continue execution"
                )
                print(
                    "  • manager.send_command('debug-session', 'q') - Quit debugger"
                )

        # Step 6: Get recent output to see what happened
        print("\n📝 Step 6: Getting session output...")
        output = manager.get_output("debug-session", lines=20)
        if output.strip():
            print("📋 Recent session output:")
            print("-" * 40)
            print(output)
            print("-" * 40)

        # Step 7: Demonstrate debugger interaction (if in debug mode)
        print("\n📝 Step 7: Testing debugger interaction...")
        current_state = manager.get_session_status("debug-session")

        if current_state.get("python_state") == "ipdb":
            print("🔧 Session is in IPDB mode - sending debug commands...")

            # List current code
            list_result = manager.send_and_wait(
                "debug-session", "l", timeout=5
            )
            print(f"📋 Code listing result: {list_result['success']}")

            # Print local variables
            vars_result = manager.send_and_wait(
                "debug-session", "pp locals()", timeout=5
            )
            print(f"📋 Variables result: {vars_result['success']}")

            # Continue execution (this will exit the debugger)
            print("▶️  Continuing execution to exit debugger...")
            continue_result = manager.send_command("debug-session", "c")
            print(f"📋 Continue result: {continue_result['success']}")

        print("\n✅ Debugging workflow demonstration complete!")

    except Exception as e:
        print(f"❌ Demo failed with error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        print("\n🧹 Cleaning up session...")
        cleanup_success = manager.cleanup_session("debug-session")
        print(f"✅ Cleanup successful: {cleanup_success}")


def demo_cipdb_agent_isolation():
    """Demonstrate CIPDB agent isolation features."""

    print("\n" + "=" * 60)
    print("🤖 CIPDB Agent Isolation Demo")
    print("=" * 60)

    # Create two managers with different agent IDs
    manager1 = PythonScreenSessionManager(
        session_name="agent1",
        session_id="agent-001",
        enable_analysis=True,
        verbose=True,
    )

    manager2 = PythonScreenSessionManager(
        session_name="agent2",
        session_id="agent-002",
        enable_analysis=True,
        verbose=True,
    )

    try:
        print(f"🤖 Agent 1 ID: {manager1.session_id}")
        print(f"🤖 Agent 2 ID: {manager2.session_id}")

        # Both agents can set up debugging with their own IDs
        print("\n📝 Setting up CIPDB for both agents...")

        session1 = manager1.create_session("isolated-debug-1")
        session2 = manager2.create_session("isolated-debug-2")

        # Attach debuggers with agent isolation
        debug1 = manager1.attach_debugger("isolated-debug-1")
        debug2 = manager2.attach_debugger("isolated-debug-2")

        print(f"✅ Agent 1 debugger setup: {debug1['success']}")
        print(f"✅ Agent 2 debugger setup: {debug2['success']}")

        if debug1["success"] and debug2["success"]:
            print("🎉 Both agents can debug independently!")
            print(
                "   Each agent's CIPDB will only trigger for their specific ID"
            )

    except Exception as e:
        print(f"❌ Agent isolation demo failed: {e}")

    finally:
        # Cleanup both sessions
        manager1.cleanup_session("isolated-debug-1")
        manager2.cleanup_session("isolated-debug-2")


def interactive_debugging_example():
    """Show how to interactively work with debugging sessions."""

    print("\n" + "=" * 60)
    print("🔍 Interactive Debugging Example")
    print("=" * 60)

    manager = PythonScreenSessionManager(enable_analysis=True, verbose=True)

    try:
        # Create session and run problematic code
        manager.create_session("interactive-debug")

        problematic_code = """
def problematic_function():
    x = [1, 2, 3]
    y = x[10]  # This will cause IndexError
    return y

try:
    result = problematic_function()
except Exception as e:
    print(f"Caught exception: {e}")
    import ipdb; ipdb.set_trace()  # Enter debugger
"""

        print("📝 Running problematic code...")
        result = manager.send_command("interactive-debug", problematic_code)

        # Wait a moment for execution
        import time

        time.sleep(2)

        # Check if we're in debug mode
        state = manager.detect_python_state("interactive-debug")
        if state["success"]:
            env_type = state["python_state"]["environment_type"]
            print(f"🔍 Current state: {env_type}")

            if env_type == "ipdb":
                print("\n🛠️  You could now interact with the debugger:")
                print(
                    "   manager.send_command('interactive-debug', 'l')    # List code"
                )
                print(
                    "   manager.send_command('interactive-debug', 'p x')  # Print variable x"
                )
                print(
                    "   manager.send_command('interactive-debug', 'u')    # Up stack frame"
                )
                print(
                    "   manager.send_command('interactive-debug', 'c')    # Continue"
                )

                # Example interaction
                print("\n📋 Example debugger interaction:")
                list_cmd = manager.send_and_wait(
                    "interactive-debug", "l", timeout=3
                )
                print(f"Code listing success: {list_cmd['success']}")

                # Exit debugger
                manager.send_command("interactive-debug", "c")

    except Exception as e:
        print(f"❌ Interactive example failed: {e}")

    finally:
        manager.cleanup_session("interactive-debug")


if __name__ == "__main__":
    print(
        "🚀 Starting PythonScreenSessionManager debugging demonstrations...\n"
    )

    # Run all demos
    demo_debugging_workflow()
    demo_cipdb_agent_isolation()
    interactive_debugging_example()

    print("\n🎉 All debugging demonstrations complete!")
    print("\n📚 Key takeaways:")
    print(
        "  • PythonScreenSessionManager can detect and manage IPDB/CIPDB sessions"
    )
    print(
        "  • State detection works for shell/python/ipython/ipdb environments"
    )
    print("  • Exception handling provides debugging suggestions")
    print("  • Agent isolation works with CIPDB conditional debugging")
    print("  • Interactive debugging commands can be sent programmatically")

# EOF
