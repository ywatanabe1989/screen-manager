"""
screen-manager: Simplified Multi-Agent Python Debugging Platform

Focused on essential functionality:
1. **cipdb**: Conditional debugging (standalone package)
2. **ScreenSessionManager**: Python process monitoring with exit code handling
3. **MCP Server**: Simple FastMCP integration for multi-agent coordination

Basic Usage:
    >>> import cipdb  # Standalone package
    >>> cipdb.set_trace(breakpoint_id="debug-agent-1")

    >>> from screen_manager import ScreenSessionManager
    >>> manager = ScreenSessionManager()
    >>> result = manager.create_session("my-task", "python script.py")
    >>> status = manager.wait_for_completion("my-task", timeout=60)
    >>> print(f"Exit code: {status['exit_code']}")
"""

__version__ = "0.1.0"
__author__ = "ywatanabe"

# Core session management functionality
from .ScreenSessionManager import ScreenSessionManager

__all__ = [
    "ScreenSessionManager",
]
