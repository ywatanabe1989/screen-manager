#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-30 07:26:40 (ywatanabe)"
# File: /home/ywatanabe/proj/screen-manager/src/screen_manager/ScreenSessionManager.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./src/screen_manager/ScreenSessionManager.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------

"""
ScreenSessionManager - Screen session management, command handling, and output retrieval.
"""

import logging
import re
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class ScreenSessionManager:
    """Manages screen sessions."""

    def __init__(
        self,
        session_name: Optional[str] = None,
        session_id: Optional[str] = None,
        working_dir: Optional[str] = None,
        verbose: Optional[bool] = False,
    ):
        """Initialize screen session manager."""
        self.session_name = session_name or "screen-manager"
        self.session_id = session_id or str(uuid.uuid4())[:8]
        self.suffix = f"{self.session_name}-{self.session_id}"
        self.working_dir = working_dir or os.getcwd()
        self._sessions = {}

        # Set up cache directory
        self.cache_dir = Path.home() / ".cache" / "screen_manager"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        if verbose:
            print(f"ScreenSessionManager initialized: {self.suffix}")

    def create_session(self, name: str, verbose=False) -> Dict[str, Any]:
        """Create new screen session without command execution."""
        session_name = self._normalize_session_name(name)

        try:
            result = subprocess.run(
                ["screen", "-dmS", session_name],
                capture_output=True,
                text=True,
                check=True,
            )

            session_info = {
                "name": session_name,
                "working_dir": self.working_dir,
                "created_at": datetime.now().isoformat(),
                "status": "created",
                "exit_code": None,
                "pid": None,
            }
            self._sessions[session_name] = session_info

            if verbose:
                print(f"Screen session creatd: {session_name}")

            # Set working directory
            self.send_command(session_name, f"cd '{self.working_dir}'")

            return {
                "success": True,
                "session_name": session_name,
                "status": "created",
                "message": f"Session {session_name} created successfully",
            }
        except subprocess.CalledProcessError as e:
            if verbose:
                print(
                    f"Failed to create screen session: {session_name}\n{e.stderr}"
                )

            return {
                "success": False,
                "error": f"Failed to create session: {e.stderr}",
                "session_name": session_name,
            }

    def send_command(
        self,
        name: str,
        command: str,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Send command to existing session (async - returns immediately)."""
        session_name = self._normalize_session_name(name)

        try:
            result = subprocess.run(
                [
                    "screen",
                    "-S",
                    session_name,
                    "-p",
                    "0",
                    "-X",
                    "stuff",
                    f"{command}\n",
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            # Update session info
            if session_name in self._sessions:
                self._sessions[session_name]["status"] = "running"
                self._sessions[session_name]["last_command"] = command

            msg = f"Sent command to {session_name} and detached:\n{command}\n\n(Note that execution of the command will take time)"
            if verbose:
                print(msg)
            return {
                "success": True,
                "message": msg,
                "command": command,
            }
        except subprocess.CalledProcessError as e:
            msg = f"Failed to send command: {e.stderr}"
            if verbose:
                print(msg)
            return {
                "success": False,
                "error": msg,
            }

    def send_commands(
        self,
        name: str,
        commands: List[str],
        delay_between_commands: float = 0.1,
        stop_on_failure: bool = True,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Send multiple commands to existing session.

        Args:
            name: Session name
            commands: List of commands to send
            delay_between_commands: Delay between sending commands (in seconds)
            stop_on_failure: If True, stop on first command failure
            verbose: Enable verbose output

        Returns:
            Dictionary with success status and execution information
        """
        session_name = self._normalize_session_name(name)

        if not commands:
            return {
                "success": False,
                "error": "No commands provided",
                "session_name": session_name,
            }

        commands_sent = []
        commands_failed = []

        try:
            import time

            for i, command in enumerate(commands):
                # Skip empty commands
                if not command.strip():
                    continue

                # Send the command
                result = self.send_command(
                    session_name, command.strip(), verbose=verbose
                )

                if result.get("success"):
                    commands_sent.append(command.strip())
                    if verbose:
                        print(
                            f"Command {i+1}/{len(commands)} sent successfully: {command.strip()}"
                        )
                else:
                    commands_failed.append(
                        {
                            "command": command.strip(),
                            "index": i,
                            "error": result.get("error", "Unknown error"),
                        }
                    )

                    if stop_on_failure:
                        error_msg = f"Command failed at index {i}: {command.strip()}. Error: {result.get('error')}"
                        if verbose:
                            print(error_msg)
                        return {
                            "success": False,
                            "error": error_msg,
                            "session_name": session_name,
                            "commands_sent": commands_sent,
                            "commands_failed": commands_failed,
                            "total_commands": len(commands),
                            "successful_commands": len(commands_sent),
                            "failed_commands": len(commands_failed),
                        }

                # Add delay between commands if specified
                if delay_between_commands > 0 and i < len(commands) - 1:
                    time.sleep(delay_between_commands)

            # Summary
            success = len(commands_failed) == 0
            msg = f"Sent {len(commands_sent)}/{len(commands)} commands to {session_name}"
            if commands_failed:
                msg += f" ({len(commands_failed)} failed)"

            if verbose:
                print(f"{msg}")
                if commands_failed:
                    print(
                        f"Failed commands: {[f['command'] for f in commands_failed]}"
                    )

            return {
                "success": success,
                "message": msg,
                "session_name": session_name,
                "commands_sent": commands_sent,
                "commands_failed": commands_failed,
                "total_commands": len(commands),
                "successful_commands": len(commands_sent),
                "failed_commands": len(commands_failed),
                "stop_on_failure": stop_on_failure,
            }

        except Exception as e:
            error_msg = f"Failed to send commands: {str(e)}"
            if verbose:
                print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "session_name": session_name,
                "commands_sent": commands_sent,
                "commands_failed": commands_failed,
            }

    def send_command_from_file(
        self,
        name: str,
        file_path: str,
        mode: str = "execute",
        delay_between_lines: float = 0.1,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Send commands from a file to existing session.

        Args:
            name: Session name
            file_path: Path to file containing commands
            mode: How to handle the file content:
                - "execute": Execute the entire file as a script
                - "lines": Send each line as a separate command
                - "source": Source the file (for shell scripts)
            delay_between_lines: Delay between sending lines (for "lines" mode)
            verbose: Enable verbose output

        Returns:
            Dictionary with success status and execution information
        """
        session_name = self._normalize_session_name(name)

        try:
            # Check if file exists
            if not os.path.isfile(file_path):
                return {
                    "success": False,
                    "error": f"File not found: {file_path}",
                    "session_name": session_name,
                }

            # Read file content
            with open(file_path, "r") as f:
                file_content = f.read().strip()

            if not file_content:
                return {
                    "success": False,
                    "error": f"File is empty: {file_path}",
                    "session_name": session_name,
                }

            commands_sent = []

            if mode == "execute":
                # Execute the file as a script
                file_extension = os.path.splitext(file_path)[1].lower()

                if file_extension == ".py":
                    command = f"python {file_path}"
                elif file_extension in [".sh", ".bash"]:
                    command = f"bash {file_path}"
                elif file_extension == ".js":
                    command = f"node {file_path}"
                else:
                    # Try to make it executable and run it
                    command = f"chmod +x {file_path} && {file_path}"

                result = self.send_command(
                    session_name, command, verbose=verbose
                )
                commands_sent.append(command)

                if not result.get("success"):
                    return result

            elif mode == "lines":
                # Send each line as a separate command
                import time

                lines = [
                    line.strip()
                    for line in file_content.split("\n")
                    if line.strip()
                ]

                for i, line in enumerate(lines):
                    if line.startswith("#"):  # Skip comments
                        continue

                    result = self.send_command(
                        session_name, line, verbose=verbose
                    )
                    commands_sent.append(line)

                    if not result.get("success"):
                        return {
                            "success": False,
                            "error": f"Failed at line {i+1}: {line}. Error: {result.get('error')}",
                            "session_name": session_name,
                            "commands_sent": commands_sent,
                        }

                    # Add delay between commands if specified
                    if delay_between_lines > 0 and i < len(lines) - 1:
                        time.sleep(delay_between_lines)

            elif mode == "source":
                # Source the file (for shell scripts)
                command = f"source {file_path}"
                result = self.send_command(
                    session_name, command, verbose=verbose
                )
                commands_sent.append(command)

                if not result.get("success"):
                    return result

            else:
                return {
                    "success": False,
                    "error": f"Unknown mode: {mode}. Use 'execute', 'lines', or 'source'",
                    "session_name": session_name,
                }

            msg = f"Sent commands from {file_path} to {session_name} (mode: {mode})"
            if verbose:
                print(f"{msg}\nCommands sent: {commands_sent}")

            return {
                "success": True,
                "message": msg,
                "session_name": session_name,
                "file_path": file_path,
                "mode": mode,
                "commands_sent": commands_sent,
                "commands_count": len(commands_sent),
            }

        except IOError as e:
            error_msg = f"Failed to read file {file_path}: {str(e)}"
            if verbose:
                print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "session_name": session_name,
            }
        except Exception as e:
            error_msg = f"Failed to send commands from file: {str(e)}"
            if verbose:
                print(error_msg)
            return {
                "success": False,
                "error": error_msg,
                "session_name": session_name,
            }

    def capture(self, name: str, n_lines: int = -1) -> str:
        """Capture the last n lines from full screen content including scrollback history."""
        content = self._capture_all(name)
        if n_lines == -1:
            return content

        lines = content.split("\n")
        if n_lines > len(lines):
            return content

        return "\n".join(lines[-n_lines:])

    def _capture_all(self, name: str) -> str:
        """Capture full screen content including scrollback history."""
        session_name = self._normalize_session_name(name)
        output_file = self.cache_dir / f"{session_name}_capture_all.txt"

        try:
            subprocess.run(
                [
                    "screen",
                    "-S",
                    session_name,
                    "-X",
                    "hardcopy",
                    "-h",
                    str(output_file),
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if output_file.exists():
                with open(output_file, "r") as f:
                    content = f.read()
                output_file.unlink()
                return content.strip()
            return ""
        except (subprocess.CalledProcessError, IOError):
            return ""

    def list_screen_sessions(
        self,
    ):
        output_file = self.cache_dir / "screen_list.txt"
        try:
            subprocess.run(
                [
                    "screen",
                    "-list",
                    "hardcopy",
                    "-h",
                    output_file,
                ],
                capture_output=True,
                text=True,
                check=True,
            )

            if output_file.exists():
                with open(output_file, "r") as f:
                    content = f.read()
                output_file.unlink()
                return content.strip()
            return ""
        except (subprocess.CalledProcessError, IOError):
            return ""

    def cleanup_session(self, name: str) -> bool:
        """Clean up session and temporary files."""
        session_name = self._normalize_session_name(name)

        print(f"Cleaning up {session_name}...")

        try:
            if self._is_screen_session_running(session_name):
                subprocess.run(
                    ["screen", "-S", session_name, "-X", "quit"],
                    capture_output=True,
                )

            # Use the new cache cleanup method
            self.cleanup_cache_files(session_name)

            if session_name in self._sessions:
                del self._sessions[session_name]
                print(f"Cleaning up successful")
            return True
        except Exception as e:
            print(f"Cleaning up failed\n{str(e)}")
            return False

    def cleanup_cache_files(self, session_name: Optional[str] = None):
        """Clean up cache files for session or all sessions."""
        try:
            if session_name:
                # Clean specific session files
                pattern = f"{self._normalize_session_name(session_name)}.*"
            else:
                # Clean all files for this manager instance
                pattern = f"*{self.suffix}*"

            for file_path in self.cache_dir.glob(pattern):
                try:
                    file_path.unlink()
                except OSError:
                    pass

            # Also clean lock files
            for lock_file in self.cache_dir.glob(f"{pattern}.lock"):
                try:
                    lock_file.unlink()
                except OSError:
                    pass

        except Exception as e:
            logger.warning(f"Failed to cleanup cache files: {e}")

    def _is_screen_session_running(self, session_name: str) -> bool:
        """Check if a screen session is currently running."""
        try:
            result = subprocess.run(
                ["screen", "-ls"],
                capture_output=True,
                text=True,
            )
            # Parse screen -ls output to find our session
            return session_name in result.stdout
        except subprocess.CalledProcessError:
            return False

    def list_sessions_info(self):
        """List information about tracked sessions."""
        return list(self._sessions.values())

    def list_sessions(self, all_sessions: bool = False) -> Dict[str, Any]:
        """List screen sessions.

        Args:
            all_sessions: If True, list all screen sessions. If False, only list sessions created by this manager.

        Returns:
            Dictionary with session list and status information
        """
        try:
            result = subprocess.run(
                ["screen", "-ls"],
                capture_output=True,
                text=True,
            )

            if all_sessions:
                # Parse all sessions from screen -ls output
                sessions = self._parse_screen_list(result.stdout)
                return {
                    "success": True,
                    "sessions": sessions,
                    "count": len(sessions),
                    "scope": "all_sessions",
                    "raw_output": result.stdout,
                }
            else:
                # Filter to only sessions managed by this instance
                managed_sessions = []
                all_sessions_list = self._parse_screen_list(result.stdout)
                for session in all_sessions_list:
                    if session.endswith(f"-{self.suffix}"):
                        managed_sessions.append(session)

                return {
                    "success": True,
                    "sessions": managed_sessions,
                    "count": len(managed_sessions),
                    "scope": "managed_sessions",
                    "managed_info": list(self._sessions.values()),
                }
        except subprocess.CalledProcessError as e:
            return {
                "success": False,
                "error": f"Failed to list sessions: {e.stderr}",
                "sessions": [],
                "count": 0,
            }

    def attach_session(
        self, name: str, verbose: bool = False
    ) -> Dict[str, Any]:
        """Attach to an existing screen session.

        Args:
            name: Name of the screen session to attach to
            verbose: Enable verbose output

        Returns:
            Dictionary with attachment information and instructions
        """
        session_name = self._normalize_session_name(name)

        # Check if session exists
        if not self._is_screen_session_running(session_name):
            return {
                "success": False,
                "error": f"Session {session_name} is not running",
                "session_name": session_name,
            }

        # Provide attachment instructions
        attach_command = f"screen -r {session_name}"

        if verbose:
            print(
                f"To attach to session {session_name}, run: {attach_command}"
            )

        return {
            "success": True,
            "session_name": session_name,
            "attach_command": attach_command,
            "message": f"To attach to session {session_name}, run: {attach_command}",
            "instructions": [
                f"Run: {attach_command}",
                "To detach: Press Ctrl+A then D",
                "To terminate session: Type 'exit' or press Ctrl+D",
            ],
        }

    def create_or_attach_session(
        self,
        name: str,
        working_dir: Optional[str] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Create a session if it doesn't exist, or provide attach instructions if it does.

        Args:
            name: Name of the screen session
            working_dir: Working directory for the session (if creating)
            verbose: Enable verbose output

        Returns:
            Dictionary with creation/attachment information
        """
        session_name = self._normalize_session_name(name)

        # Check if session already exists and is running
        if self._is_screen_session_running(session_name):
            if verbose:
                print(
                    f"Session {session_name} already exists - providing attachment instructions"
                )

            # Return attachment instructions
            attach_result = self.attach_session(name, verbose=verbose)
            attach_result["action_taken"] = "attach_existing"
            return attach_result
        else:
            if verbose:
                print(
                    f"Session {session_name} doesn't exist - creating new session"
                )

            # Set working directory if provided
            if working_dir:
                original_working_dir = self.working_dir
                self.working_dir = working_dir

            # Create new session
            create_result = self.create_session(name, verbose=verbose)

            # Restore original working directory if it was changed
            if working_dir:
                self.working_dir = original_working_dir

            create_result["action_taken"] = "create_new"
            return create_result

    # ----------------------------------------
    # Utilities
    # ----------------------------------------
    @property
    def sessions(
        self,
    ):
        return self.list_sessions_info()

    def _normalize_session_name(self, name: str) -> str:
        """Normalize session name with prefix."""
        if not name.endswith("-" + self.suffix):
            return f"{name}-{self.suffix}"
        return name

    def _parse_screen_list(self, screen_output: str) -> List[str]:
        """Parse screen -ls output to get session names."""
        # print(screen_output)
        sessions = []
        for line in screen_output.split("\n"):
            match = re.search(r"\s+(\S+)\s+", line)
            if match:
                session_id = match.group(1)
                if "." in session_id:
                    session_name = session_id.split(".", 1)[1]
                    sessions.append(session_name)
        return sessions

    def _get_cache_file(self, session_name: str, suffix: str) -> str:
        """Get cache file path for session."""
        return str(self.cache_dir / f"{session_name}.{suffix}")


def main():
    import time
    from pprint import pprint

    from screen_manager import ScreenSessionManager

    # Instantiate ScreenSessionManager
    manager = ScreenSessionManager(verbose=True)

    # Create a test session
    _result = manager.create_session("demo", verbose=True)

    # Demonstrate async send_command (fire-and-forget)
    command = "python ./examples/script_with_cipdb.py"
    async_result = manager.send_command(
        "demo",
        command,
        verbose=True,
    )

    # Capture the last 10 lines of screen session in the same format as human programmer can see
    print(manager.capture("demo", 10))


if __name__ == "__main__":
    main()

# python -m screen_manager.ScreenSessionManager

# EOF
