#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-30 09:24:53 (ywatanabe)"
# File: /home/ywatanabe/proj/screen-session-manager/src/screen_session_manager/mcp_server.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./src/screen_session_manager/mcp_server.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------
!/usr/bin/env python3

"""
MCP Server for Screen Session Manager

Provides MCP tools for managing screen sessions, sending commands, and capturing output.
"""

import logging
from typing import Any
from typing import Dict
from typing import List, Optional

from fastmcp import FastMCP
from pydantic import Field

try:
    from .ScreenSessionManager import ScreenSessionManager
except ImportError:
    from ScreenSessionManager import ScreenSessionManager

logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("Screen Session Manager")

# Global session manager instance
_session_manager: Optional[ScreenSessionManager] = None


def get_session_manager() -> ScreenSessionManager:
    """Get or create the global session manager instance."""
    global _session_manager
    if _session_manager is None:
        _session_manager = ScreenSessionManager()
    return _session_manager


@mcp.tool
def create_session(
    name: str = Field(description="Name for the screen session"),
    working_dir: Optional[str] = Field(
        default=None, description="Working directory for the session (defaults to current directory)"
    ),
    verbose: bool = Field(default=False, description="Enable verbose output"),
) -> Dict[str, Any]:
    """Create a new screen session.

    IMPORTANT: The session name will be automatically suffixed with a unique identifier
    (e.g., 'test' becomes 'test-screen-manager-abc123'). Use the returned
    'session_name' field for all subsequent operations.

    Args:
        name: Base name for the screen session (will be auto-suffixed)
        working_dir: Working directory for the session (defaults to current directory)
        verbose: Enable verbose output for debugging

    Returns:
        Dictionary with:
        - success: Boolean indicating if creation succeeded
        - session_name: Full session name to use in subsequent commands
        - status: 'created' if successful
        - message: Human-readable status message
        - error: Error message if failed
    """
    try:
        manager = get_session_manager()
        if working_dir:
            manager.working_dir = working_dir

        result = manager.create_session(name, verbose=verbose)
        logger.info(f"Created session: {name}")
        return result
    except Exception as e:
        logger.error(f"Failed to create session {name}: {e}")
        return {
            "success": False,
            "error": f"Failed to create session: {str(e)}",
            "session_name": name,
        }


@mcp.tool
def send_command(
    session_name: str = Field(description="Full name of the screen session (as returned by create_session)"),
    command: str = Field(description="Command to send to the session"),
    verbose: bool = Field(default=False, description="Enable verbose output"),
) -> Dict[str, Any]:
    """Send a command to an existing screen session.

    NOTE: Commands are sent asynchronously and return immediately. The command
    may still be executing when this function returns. To check if a command
    has completed, capture the output and look for a shell prompt (e.g., '$').

    For interactive commands (like ipdb), send each interaction as a separate command.

    Args:
        session_name: Full session name (use the exact name returned by create_session)
        command: Command to send to the session (newline is added automatically)
        verbose: Enable verbose output for debugging

    Returns:
        Dictionary with:
        - success: Boolean indicating if command was sent successfully
        - message: Status message including the command sent
        - command: The command that was sent
        - error: Error message if failed
    """
    try:
        manager = get_session_manager()
        result = manager.send_command(session_name, command, verbose=verbose)
        logger.info(f"Sent command to {session_name}: {command}")
        return result
    except Exception as e:
        logger.error(f"Failed to send command to {session_name}: {e}")
        return {
            "success": False,
            "error": f"Failed to send command: {str(e)}",
            "command": command,
        }


@mcp.tool
def capture_output(
    session_name: str = Field(description="Full name of the screen session (as returned by create_session)"),
    num_last_lines: int = Field(
        default=-1, description="Number of last lines to capture (-1 for all available output, positive number for last N lines)"
    ),
) -> Dict[str, Any]:
    """Capture output from a screen session.

    This captures the current screen buffer content. For best results:
    - Use num_last_lines=-1 to capture all available output
    - Wait 1-2 seconds after sending commands before capturing

    To detect command completion, check if the last non-empty line matches your prompt:
    - Shell: ends with '$ ' or '# ' (but PS1 is user-customizable)
    - Python: exactly '>>> ' or '... '
    - IPython: starts with 'In [' and ends with ']: '
    - ipdb: starts with 'ipdb> '

    Note: Prompt detection is inherently unreliable since users can customize prompts.
    Consider using timeouts or command-specific markers for critical operations

    Args:
        session_name: Full session name (use the exact name returned by create_session)
        num_last_lines: Number of last lines to capture:
                        -1 = all available output (recommended)
                        N = last N lines from the buffer

    Returns:
        Dictionary with:
        - success: Boolean indicating if capture succeeded
        - output: The captured text output
        - session_name: The session name used
        - lines_captured: Number of lines actually captured
        - error: Error message if failed
    """
    try:
        manager = get_session_manager()
        output = manager.capture(session_name, n_lines=num_last_lines)
        logger.info(
            f"Captured {len(output.split(chr(10)))} lines from {session_name}"
        )
        return {
            "success": True,
            "output": output,
            "session_name": session_name,
            "lines_captured": len(output.split("\n")) if output else 0,
        }
    except Exception as e:
        logger.error(f"Failed to capture output from {session_name}: {e}")
        return {
            "success": False,
            "error": f"Failed to capture output: {str(e)}",
            "session_name": session_name,
        }


@mcp.tool
def list_sessions() -> Dict[str, Any]:
    """List all active screen sessions managed by this instance.

    Returns:
        Dictionary with list of sessions and their information
    """
    try:
        manager = get_session_manager()
        sessions = manager.sessions
        logger.info(f"Retrieved {len(sessions)} sessions")
        return {
            "success": True,
            "sessions": sessions,
            "count": len(sessions),
        }
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return {
            "success": False,
            "error": f"Failed to list sessions: {str(e)}",
            "sessions": [],
            "count": 0,
        }


@mcp.tool
def cleanup_session(
    session_name: str = Field(
        description="Full name of the screen session to cleanup (as returned by create_session)"
    ),
) -> Dict[str, Any]:
    """Clean up a screen session and remove temporary files.

    This will:
    - Terminate the screen session
    - Remove any temporary files associated with the session
    - Clean up the session from internal tracking

    Args:
        session_name: Full session name (use the exact name returned by create_session)

    Returns:
        Dictionary with:
        - success: Boolean indicating if cleanup succeeded
        - message: Status message
        - session_name: The session that was cleaned up
        - error: Error message if cleanup failed
    """
    try:
        manager = get_session_manager()
        success = manager.cleanup_session(session_name)
        if success:
            logger.info(f"Successfully cleaned up session: {session_name}")
            return {
                "success": True,
                "message": f"Session {session_name} cleaned up successfully",
                "session_name": session_name,
            }
        else:
            logger.warning(f"Failed to cleanup session: {session_name}")
            return {
                "success": False,
                "error": f"Failed to cleanup session {session_name}",
                "session_name": session_name,
            }
    except Exception as e:
        logger.error(f"Exception during cleanup of {session_name}: {e}")
        return {
            "success": False,
            "error": f"Exception during cleanup: {str(e)}",
            "session_name": session_name,
        }


@mcp.tool
def get_session_info(
    session_name: str = Field(description="Full name of the screen session (as returned by create_session)"),
) -> Dict[str, Any]:
    """Get detailed information about a specific screen session.

    Args:
        session_name: Full session name (use the exact name returned by create_session)

    Returns:
        Dictionary with:
        - success: Boolean indicating if session was found
        - session_info: Dictionary containing session details (name, working_dir, created_at, status, last_command)
        - session_name: The session name queried
        - error: Error message if session not found
    """
    try:
        manager = get_session_manager()
        sessions = manager.sessions

        # Find the session by name
        session_info = None
        for session in sessions:
            if isinstance(session, dict) and session.get(
                "name"
            ) == manager._normalize_session_name(session_name):
                session_info = session
                break

        if session_info:
            logger.info(f"Retrieved info for session: {session_name}")
            return {
                "success": True,
                "session_info": session_info,
                "session_name": session_name,
            }
        else:
            logger.warning(f"Session not found: {session_name}")
            return {
                "success": False,
                "error": f"Session {session_name} not found",
                "session_name": session_name,
            }
    except Exception as e:
        logger.error(f"Failed to get session info for {session_name}: {e}")
        return {
            "success": False,
            "error": f"Failed to get session info: {str(e)}",
            "session_name": session_name,
        }


@mcp.tool
def send_commands(
    session_name: str = Field(description="Full name of the screen session (as returned by create_session)"),
    commands: List[str] = Field(
        description="List of commands to send to the session sequentially"
    ),
    delay_between_commands: float = Field(
        default=0.1, description="Delay between sending commands in seconds (increase for slow commands)"
    ),
    stop_on_failure: bool = Field(
        default=True, description="If True, stop on first command failure"
    ),
    verbose: bool = Field(default=False, description="Enable verbose output"),
) -> Dict[str, Any]:
    """Send multiple commands to an existing screen session sequentially.

    Useful for:
    - Sending a series of shell commands
    - Interacting with interactive programs (Python REPL, ipdb, etc.)
    - Automating multi-step processes

    Note: Commands are sent with delays between them. Increase delay_between_commands
    for commands that take longer to execute.

    Args:
        session_name: Full session name (use the exact name returned by create_session)
        commands: List of commands to send sequentially
        delay_between_commands: Seconds to wait between commands (default 0.1, increase for slow operations)
        stop_on_failure: If True, stop sending if a command fails
        verbose: Enable verbose output for debugging

    Returns:
        Dictionary with:
        - success: Boolean indicating overall success
        - commands_sent: List of successfully sent commands
        - commands_failed: List of failed commands
        - total_commands: Total number of commands attempted
        - successful_commands: Count of successful commands
        - failed_commands: Count of failed commands
    """
    try:
        manager = get_session_manager()
        result = manager.send_commands(
            session_name,
            commands,
            delay_between_commands=delay_between_commands,
            stop_on_failure=stop_on_failure,
            verbose=verbose,
        )

        if result.get("success"):
            logger.info(
                f"Sent {result.get('successful_commands', 0)}/{result.get('total_commands', 0)} commands to {session_name}"
            )
        else:
            logger.warning(
                f"Failed to send commands to {session_name}: {result.get('error')}"
            )

        return result
    except Exception as e:
        logger.error(f"Failed to send commands to {session_name}: {e}")
        return {
            "success": False,
            "error": f"Failed to send commands: {str(e)}",
            "session_name": session_name,
        }


@mcp.tool
def send_command_from_file(
    session_name: str = Field(description="Name of the screen session"),
    file_path: str = Field(description="Path to file containing commands"),
    mode: str = Field(
        default="execute",
        description="How to handle file: 'execute', 'lines', or 'source'",
    ),
    delay_between_lines: float = Field(
        default=0.1,
        description="Delay between sending lines (for 'lines' mode)",
    ),
    verbose: bool = Field(default=False, description="Enable verbose output"),
) -> Dict[str, Any]:
    """Send commands from a file to an existing screen session.

    Args:
        session_name: Name of the screen session
        file_path: Path to file containing commands
        mode: How to handle the file content:
            - "execute": Execute the entire file as a script (detects by extension)
            - "lines": Send each line as a separate command
            - "source": Source the file (for shell scripts)
        delay_between_lines: Delay between sending lines (for "lines" mode)
        verbose: Enable verbose output

    Returns:
        Dictionary with success status and execution information
    """
    try:
        manager = get_session_manager()
        result = manager.send_command_from_file(
            session_name,
            file_path,
            mode=mode,
            delay_between_lines=delay_between_lines,
            verbose=verbose,
        )

        if result.get("success"):
            logger.info(
                f"Sent commands from file {file_path} to {session_name} (mode: {mode}, {result.get('commands_count', 0)} commands)"
            )
        else:
            logger.warning(
                f"Failed to send commands from file {file_path}: {result.get('error')}"
            )

        return result
    except Exception as e:
        logger.error(
            f"Failed to send commands from file {file_path} to {session_name}: {e}"
        )
        return {
            "success": False,
            "error": f"Failed to send commands from file: {str(e)}",
            "session_name": session_name,
            "file_path": file_path,
        }


@mcp.tool
def list_all_sessions(
    all_sessions: bool = Field(
        default=False,
        description="If True, list all screen sessions. If False, only managed sessions",
    )
) -> Dict[str, Any]:
    """List screen sessions with filtering options.

    NOTE: Sessions marked as "Dead ???" are zombie sessions that failed to terminate
    properly. These can be safely ignored and cleaned up with 'screen -wipe' command.
    Only "Attached" and "Detached" sessions are actually running.

    Args:
        all_sessions: If True, list all screen sessions including dead ones.
                      If False, only list sessions created by this manager.

    Returns:
        Dictionary with:
        - success: Boolean indicating if listing succeeded
        - sessions: List of session names (ignores dead sessions)
        - count: Number of active sessions
        - scope: 'all_sessions' or 'managed_sessions'
        - raw_output: Full screen -list output including dead sessions
    """
    try:
        manager = get_session_manager()
        result = manager.list_sessions(all_sessions=all_sessions)
        logger.info(
            f"Listed {result.get('count', 0)} sessions (scope: {result.get('scope', 'unknown')})"
        )
        return result
    except Exception as e:
        logger.error(f"Failed to list sessions: {e}")
        return {
            "success": False,
            "error": f"Failed to list sessions: {str(e)}",
            "sessions": [],
            "count": 0,
        }


@mcp.tool
def attach_session(
    session_name: str = Field(
        description="Name of the screen session to attach to"
    ),
    verbose: bool = Field(default=False, description="Enable verbose output"),
) -> Dict[str, Any]:
    """Get instructions for attaching to an existing screen session.

    Args:
        session_name: Name of the screen session to attach to
        verbose: Enable verbose output

    Returns:
        Dictionary with attachment instructions and commands
    """
    try:
        manager = get_session_manager()
        result = manager.attach_session(session_name, verbose=verbose)
        if result.get("success"):
            logger.info(
                f"Provided attachment instructions for session: {session_name}"
            )
        else:
            logger.warning(
                f"Failed to provide attachment instructions: {result.get('error')}"
            )
        return result
    except Exception as e:
        logger.error(
            f"Failed to get attachment instructions for {session_name}: {e}"
        )
        return {
            "success": False,
            "error": f"Failed to get attachment instructions: {str(e)}",
            "session_name": session_name,
        }


@mcp.tool
def create_or_attach_session(
    name: str = Field(description="Name for the screen session"),
    working_dir: Optional[str] = Field(
        default=None,
        description="Working directory for the session (if creating)",
    ),
    verbose: bool = Field(default=False, description="Enable verbose output"),
) -> Dict[str, Any]:
    """Create a session if it doesn't exist, or provide attach instructions if it does.

    This is a convenience method that will:
    - Create a new session if none exists with the given name
    - Provide attachment instructions if a session already exists

    Args:
        name: Name for the screen session
        working_dir: Working directory for the session (only used if creating new session)
        verbose: Enable verbose output

    Returns:
        Dictionary with creation/attachment information and action taken
    """
    try:
        manager = get_session_manager()
        result = manager.create_or_attach_session(
            name, working_dir=working_dir, verbose=verbose
        )

        action = result.get("action_taken", "unknown")
        if action == "create_new":
            logger.info(f"Created new session: {name}")
        elif action == "attach_existing":
            logger.info(
                f"Provided attachment instructions for existing session: {name}"
            )

        return result
    except Exception as e:
        logger.error(f"Failed to create or attach session {name}: {e}")
        return {
            "success": False,
            "error": f"Failed to create or attach session: {str(e)}",
            "session_name": name,
        }


def main():
    """Run the MCP server."""
    try:
        logger.info("Starting Screen Session Manager MCP Server")
        mcp.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        raise


if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    main()

# python -m screen_manager.mcp_server

# EOF
