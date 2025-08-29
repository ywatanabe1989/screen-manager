#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Timestamp: "2025-08-29 17:43:57 (ywatanabe)"
# File: /home/ywatanabe/proj/emacs_ipython_ipdb_server/emacs_ipython_ipdb_server/emacs_ipython_server.py
# ----------------------------------------
from __future__ import annotations
import os
__FILE__ = (
    "./emacs_ipython_ipdb_server/emacs_ipython_ipdb_server/emacs_ipython_server.py"
)
__DIR__ = os.path.dirname(__FILE__)
# ----------------------------------------
"""emacs-ipython-mcp-server: iPython Agent Development Server.

MCP server that discovers and interacts with existing iPython sessions in Emacs buffers.
"""

import argparse
import asyncio
import json
import logging
import re
import subprocess
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

import mcp.types as types
from mcp.server import Server


@dataclass
class BufferInfo:
    """Information about an Emacs buffer."""

    name: str
    type: str  # "ipython", "python", "vterm"
    process_type: Optional[str] = None  # "ipython", "python3", "ipdb"
    buffer_content: str = ""
    last_output: str = ""
    working_directory: str = ""
    process_id: Optional[int] = None


@dataclass
class SessionContext:
    """Context information about a discovered session."""

    buffer_name: str
    session_type: str  # "ipython", "ipdb"
    current_state: str  # "idle", "running", "debug", "error"
    variables: Dict[str, Any] = field(default_factory=dict)
    recent_commands: List[str] = field(default_factory=list)
    current_namespace: Optional[str] = None


class EmacsIPythonServer:
    """MCP Server for discovering and interacting with existing iPython sessions."""

    def __init__(self, config_path: str = None):
        self.server = Server("emacs-ipython-mcp-server")
        self.discovered_buffers: Dict[str, BufferInfo] = {}
        self.session_contexts: Dict[str, SessionContext] = {}
        self.emacs_server_name: Optional[str] = None

        self.setup_handlers()

    async def initialize(self):
        """Initialize the iPython server components."""
        await self.connect_to_emacs()
        logging.info("Emacs iPython MCP Server initialized successfully")

    # Emacs Integration Methods
    async def connect_to_emacs(self) -> Dict[str, Any]:
        """Connect to running Emacs server."""
        try:
            # Test connection with a simple buffer count
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    "(length (buffer-list))",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                buffer_count = result.stdout.strip()
                return {"status": "success", "buffer_count": buffer_count}
            else:
                return {
                    "status": "error",
                    "message": f"No Emacs server found: {result.stderr}",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to connect: {str(e)}",
            }

    async def get_buffer_list(self) -> List[Dict[str, Any]]:
        """List all buffers in Emacs."""
        try:
            # Get buffer list from Emacs
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    "(mapcar (lambda (buf) (list (buffer-name buf) (buffer-file-name buf) (with-current-buffer buf major-mode))) (buffer-list))",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse the elisp result - this is a simplified parser
                buffer_data = result.stdout.strip()
                buffers = []
                # TODO: Implement proper elisp parsing
                return buffers
            else:
                return []
        except Exception as e:
            logging.error(f"Failed to get buffer list: {e}")
            return []

    # Session Discovery Methods
    async def find_ipython_buffers(self) -> List[Dict[str, Any]]:
        """Discover active iPython sessions in Emacs buffers."""
        try:
            # Look for buffers with iPython processes
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    """(let ((ipython-buffers '()))
                     (dolist (buf (buffer-list))
                       (with-current-buffer buf
                         (when (or (string-match "\\*IPython" (buffer-name))
                                   (string-match "\\*Python" (buffer-name))
                                   (and (eq major-mode 'vterm-mode)
                                        (string-match "ipython\\|python3" (or (buffer-string) ""))))
                           (push (list (buffer-name)
                                       (symbol-name major-mode)
                                       (if (boundp 'vterm--process)
                                           (process-command vterm--process)
                                           nil)) ipython-buffers))))
                     ipython-buffers)""",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Parse and store discovered buffers
                discovered = []
                # TODO: Parse elisp output properly
                logging.info(f"Found iPython buffers: {result.stdout}")
                return discovered
            else:
                return []
        except Exception as e:
            logging.error(f"Failed to find iPython buffers: {e}")
            return []

    async def list_ipython_sessions(self) -> Dict[str, Any]:
        """Enhanced session listing with detailed info and selection IDs."""
        try:
            # Get all vterm buffers with iPython
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    """(let ((sessions '()) (id-counter 1))
                     (dolist (buf (buffer-list))
                       (with-current-buffer buf
                         (when (and (eq major-mode 'vterm-mode)
                                    (or (string-match "ipython" (buffer-string))
                                        (string-match "In \\[[0-9]+\\]:" (buffer-string))))
                           (let* ((buffer-name (buffer-name))
                                  (last-output (buffer-substring-no-properties
                                               (max (point-min) (- (point-max) 1000))
                                               (point-max)))
                                  (session-info (list
                                                id-counter
                                                buffer-name
                                                major-mode
                                                last-output)))
                             (push session-info sessions)
                             (setq id-counter (+ id-counter 1))))))
                     sessions)""",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                sessions = []
                # Parse the elisp output (simplified parsing)
                raw_output = result.stdout.strip()
                if raw_output and raw_output != "nil":
                    # For now, create mock sessions since elisp parsing is complex
                    # This would be replaced with proper elisp parsing
                    buffer_names = await self._get_buffer_names_with_ipython()

                    for i, buffer_name in enumerate(buffer_names, 1):
                        session_info = await self._analyze_session_detailed(
                            buffer_name, i
                        )
                        if session_info:
                            sessions.append(session_info)

                return {
                    "success": True,
                    "sessions": sessions,
                    "count": len(sessions),
                }
            else:
                return {
                    "success": True,
                    "sessions": [],
                    "count": 0,
                    "message": "No iPython sessions found",
                }
        except Exception as e:
            logging.error(f"Failed to list iPython sessions: {e}")
            return {
                "success": False,
                "error": str(e),
                "sessions": [],
                "count": 0,
            }

    async def _get_buffer_names_with_ipython(self) -> List[str]:
        """Get buffer names that have iPython running."""
        try:
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    """(let ((buffers '()))
                     (dolist (buf (buffer-list))
                       (with-current-buffer buf
                         (when (and (eq major-mode 'vterm-mode)
                                    (or (string-match "ipython" (buffer-string))
                                        (string-match "In \\[[0-9]+\\]:" (buffer-string))))
                           (push (buffer-name) buffers))))
                     buffers)""",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                # Simple parsing - extract buffer names from elisp output
                output = result.stdout.strip()
                if output and output != "nil":
                    # Mock buffer names for now - in reality would parse elisp properly
                    return [
                        "*vterm*",
                        "*vterm*<2>",
                        "*Python*",
                    ]  # Common names
                return []
            return []
        except Exception as e:
            logging.error(f"Failed to get buffer names: {e}")
            return []

    async def _analyze_session_detailed(
        self, buffer_name: str, session_id: int
    ) -> Dict[str, Any]:
        """Analyze a session in detail for the session list."""
        try:
            # Get recent output
            output_result = await self.get_buffer_output(buffer_name, lines=50)
            if output_result["status"] != "success":
                return None

            output = output_result["output"]

            # Get detailed session status using prompt-based detection
            detailed_status = await self._detect_session_status_from_prompt(
                output
            )
            is_busy = detailed_status in ["ipdb", "ipython_busy", "busy"]

            # Get current working directory
            pwd = None
            if not is_busy and detailed_status == "ipython_idle":
                pwd_result = await self.send_code_to_ipython(
                    buffer_name, "import os; print(f'PWD:{os.getcwd()}')"
                )
                if pwd_result["status"] == "success":
                    # Wait a moment for output
                    await asyncio.sleep(0.5)
                    pwd_output = await self.get_buffer_output(
                        buffer_name, lines=5
                    )
                    if pwd_output["status"] == "success":
                        pwd_match = re.search(
                            r"PWD:([^\n\r]+)", pwd_output["output"]
                        )
                        if pwd_match:
                            pwd = pwd_match.group(1).strip()

            # Extract current iPython input number
            ipython_prompt = re.search(r"In \[(\d+)\]:", output)
            current_input = (
                ipython_prompt.group(1) if ipython_prompt else "unknown"
            )

            # Detect errors
            has_error = "Traceback" in output or "Error:" in output

            # Map detailed status to simple status for backward compatibility
            simple_status = "busy" if is_busy else "idle"

            return {
                "id": session_id,
                "buffer_name": buffer_name,
                "status": simple_status,
                "detailed_status": detailed_status,  # New field with prompt-based status
                "current_input_number": current_input,
                "working_directory": pwd,
                "has_recent_error": has_error,
                "last_output_preview": (
                    output[-200:] if len(output) > 200 else output
                ),
                "project": self._identify_project(pwd) if pwd else "unknown",
            }

        except Exception as e:
            logging.error(f"Failed to analyze session {buffer_name}: {e}")
            return None

    async def _check_if_session_busy(
        self, buffer_name: str, monitor_seconds: int = 3
    ) -> bool:
        """Check if iPython session is busy by analyzing prompt patterns."""
        try:
            # Get current buffer content (more lines for better prompt detection)
            buffer_output = await self.get_buffer_output(buffer_name, lines=20)
            if buffer_output["status"] != "success":
                return False

            buffer_content = buffer_output["output"]

            # Check current session status based on prompts
            session_status = await self._detect_session_status_from_prompt(
                buffer_content
            )

            if session_status in ["ipdb", "ipython_busy", "busy"]:
                return True
            elif session_status in ["ipython_idle", "shell"]:
                return False

            # For ambiguous cases, do a quick monitoring approach
            # Test responsiveness with a minimal command
            test_result = await self._test_session_responsiveness(buffer_name)
            return not test_result

        except Exception as e:
            logging.error(f"Error checking session busy status: {e}")
            return False

    async def _detect_session_status_from_prompt(
        self, buffer_content: str
    ) -> str:
        """Detect current session status from prompt patterns.
        Returns: 'ipython_idle', 'ipython_busy', 'ipdb', 'shell', 'unknown'
        """
        try:
            lines = buffer_content.split("\n")

            # Check from the end of buffer backwards for recent prompts
            for i in range(len(lines) - 1, max(-1, len(lines) - 10), -1):
                line = lines[i].strip()

                # Check for IPDB prompt (highest priority - always indicates active debugging)
                if re.match(r"^(\(Pdb\)|ipdb>)", line):
                    return "ipdb"

                # Check for IPython In[] prompt
                if re.match(r"^In \[\d+\]:", line):
                    # If this is the last meaningful line, IPython is ready for input
                    remaining_lines = [
                        l.strip() for l in lines[i + 1 :] if l.strip()
                    ]
                    if not remaining_lines:
                        return "ipython_idle"
                    # If there's content after In[] prompt, check if it's execution output
                    return "ipython_busy"

                # Check for IPython Out[] prompt - indicates recent completion
                if re.match(r"^Out\[\d+\]:", line):
                    # Check if there's a following In[] prompt (ready for new input)
                    for j in range(i + 1, min(len(lines), i + 5)):
                        next_line = lines[j].strip()
                        if re.match(r"^In \[\d+\]:", next_line):
                            # Check what's after the In[] prompt
                            remaining = [
                                l.strip() for l in lines[j + 1 :] if l.strip()
                            ]
                            return (
                                "ipython_idle"
                                if not remaining
                                else "ipython_busy"
                            )
                    return "ipython_idle"

                # Check for shell prompt
                if re.match(r"^.*[$#]\s*$", line):
                    return "shell"

                # Check for execution indicators suggesting busy state
                if any(
                    indicator in line.lower()
                    for indicator in [
                        "executing",
                        "running",
                        "traceback (most recent call last)",
                        "keyboardinterrupt",
                        "processing",
                        "working...",
                    ]
                ):
                    return "ipython_busy"

            # Check for embedded IPython patterns
            buffer_lower = buffer_content.lower()
            if (
                "ipython console for" in buffer_lower
                or "embedded ipython" in buffer_lower
            ):
                # Look for the most recent In[] pattern
                if re.search(
                    r"in \[\d+\]:\s*$",
                    buffer_content,
                    re.IGNORECASE | re.MULTILINE,
                ):
                    return "ipython_idle"
                elif re.search(r"in \[\d+\]:", buffer_content, re.IGNORECASE):
                    return "ipython_busy"

            return "unknown"

        except Exception as e:
            logging.error(f"Error detecting session status: {e}")
            return "unknown"

    async def _test_session_responsiveness(self, buffer_name: str) -> bool:
        """Test if session is responsive by sending a minimal command.
        Returns True if responsive, False if busy/unresponsive.
        """
        try:
            # Send a simple command that should respond quickly
            # Using a pass statement that won't affect the session
            test_command = "pass"

            # Get initial buffer state
            initial_output = await self.get_buffer_output(buffer_name, lines=5)
            if initial_output["status"] != "success":
                return False

            initial_content = initial_output["output"]
            initial_lines = len(initial_content.split("\n"))

            # Send test command
            await self._send_string_to_buffer(buffer_name, test_command + "\n")

            # Wait briefly and check for response
            await asyncio.sleep(1.0)

            final_output = await self.get_buffer_output(buffer_name, lines=5)
            if final_output["status"] != "success":
                return False

            new_content = final_output["output"]

            # Look for new In[] prompt indicating responsiveness
            if re.search(r"In \[\d+\]:\s*$", new_content, re.MULTILINE):
                return True

            # Also check if we got any new content suggesting activity
            return len(new_content) > len(initial_content)

        except Exception as e:
            logging.error(f"Error testing session responsiveness: {e}")
            return False

    def _identify_project(self, pwd: str) -> str:
        """Identify project based on working directory."""
        if not pwd:
            return "unknown"

        # Extract project name from path
        import os

        project_name = os.path.basename(pwd)

        # Common project indicators
        if any(
            keyword in project_name.lower()
            for keyword in ["proj", "project", "work"]
        ):
            return project_name

        # Look at parent directory structure
        path_parts = pwd.split(os.sep)
        for part in reversed(path_parts):
            if any(
                keyword in part.lower()
                for keyword in ["proj", "project", "work", "dev", "code"]
            ):
                return part

        return project_name or "unknown"

    async def prompt_session_selection(self) -> Dict[str, Any]:
        """Prompt user to select which iPython session to work with."""
        try:
            sessions = await self.list_ipython_sessions()

            if not sessions:
                return {
                    "status": "info",
                    "message": "No iPython sessions found",
                    "suggestion": "Start iPython in Emacs vterm first",
                }

            # Format session list for easy selection
            selection_text = (
                "\n🐍 Available iPython Sessions:\n" + "=" * 50 + "\n"
            )

            for session in sessions:
                # Enhanced status icons based on detailed status
                detailed = session.get("detailed_status", session["status"])
                if detailed == "ipdb":
                    status_icon = "🐛"  # IPDB debugging
                    status_text = "IPDB (Debugging)"
                elif detailed == "ipython_busy":
                    status_icon = "⚡"  # Busy executing
                    status_text = "BUSY (Executing)"
                elif detailed == "ipython_idle":
                    status_icon = "💤"  # Ready for input
                    status_text = "IDLE (Ready)"
                elif detailed == "shell":
                    status_icon = "🐚"  # Shell mode
                    status_text = "SHELL (Terminal)"
                else:
                    status_icon = "❓"  # Unknown
                    status_text = f"{session['status'].upper()} ({detailed})"

                error_icon = "❌" if session["has_recent_error"] else "✅"

                selection_text += f"[{session['id']}] {status_icon} {session['buffer_name']}\n"
                selection_text += f"    Status: {status_text}\n"
                selection_text += f"    Project: {session['project']}\n"
                selection_text += f"    Directory: {session['working_directory'] or 'unknown'}\n"
                selection_text += f"    Input#: {session['current_input_number']} {error_icon}\n"

                if session["status"] == "busy":
                    selection_text += f"    Preview: ...{session['last_output_preview'][-100:]}\n"

                selection_text += "-" * 40 + "\n"

            selection_text += "\n💡 Usage: Use session ID (1, 2, 3...) to select which session to work with"

            return {
                "status": "success",
                "sessions": sessions,
                "selection_display": selection_text,
                "session_count": len(sessions),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get session selection: {str(e)}",
            }

    async def select_session_by_id(self, session_id: int) -> Dict[str, Any]:
        """Select a session by its ID for subsequent operations."""
        try:
            sessions = await self.list_ipython_sessions()

            selected_session = next(
                (s for s in sessions if s["id"] == session_id), None
            )

            if not selected_session:
                return {
                    "status": "error",
                    "message": f"Session ID {session_id} not found",
                    "available_ids": [s["id"] for s in sessions],
                }

            # Store selected session in context
            self.session_contexts[f"selected_session"] = {
                "buffer_name": selected_session["buffer_name"],
                "session_id": session_id,
                "selected_at": datetime.now().isoformat(),
            }

            return {
                "status": "success",
                "selected_session": selected_session,
                "message": f"Selected session {session_id}: {selected_session['buffer_name']}",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to select session: {str(e)}",
            }

    async def get_selected_session(self) -> Dict[str, Any]:
        """Get currently selected session information."""
        if "selected_session" not in self.session_contexts:
            return {
                "status": "info",
                "message": "No session selected. Use prompt_session_selection() first.",
            }

        return {
            "status": "success",
            "selected": self.session_contexts["selected_session"],
        }

    async def find_ipdb_sessions(self) -> List[Dict[str, Any]]:
        """Locate active IPDB debugging sessions in vterm."""
        try:
            # Look for vterm buffers with IPDB prompts
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    """(let ((ipdb-buffers '()))
                     (dolist (buf (buffer-list))
                       (with-current-buffer buf
                         (when (and (eq major-mode 'vterm-mode)
                                    (string-match "(Pdb)" (buffer-string)))
                           (push (list (buffer-name)
                                       "ipdb"
                                       (point)
                                       (buffer-substring-no-properties
                                        (max (point-min) (- (point-max) 500))
                                        (point-max))) ipdb-buffers))))
                     ipdb-buffers)""",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                logging.info(f"Found IPDB sessions: {result.stdout}")
                return []  # TODO: Parse elisp output
            else:
                return []
        except Exception as e:
            logging.error(f"Failed to find IPDB sessions: {e}")
            return []

    # Interactive Communication Methods
    async def send_code_to_ipython(
        self, buffer_name: str, code: str
    ) -> Dict[str, Any]:
        """Send code to existing iPython session."""
        try:
            # Send code to the iPython buffer via Emacs
            escaped_code = code.replace('"', '\\"').replace("\n", "\\n")
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    f"""(with-current-buffer "{buffer_name}"
                      (if (eq major-mode 'vterm-mode)
                          (progn
                            (vterm-send-string "{escaped_code}")
                            (vterm-send-return)
                            "sent-to-vterm")
                        (progn
                          (goto-char (point-max))
                          (insert "{escaped_code}")
                          (comint-send-input)
                          "sent-to-comint")))""",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "buffer_name": buffer_name,
                    "code": code,
                    "method": result.stdout.strip().strip('"'),
                }
            else:
                return {"status": "error", "message": "Failed to send code"}
        except Exception as e:
            return {"status": "error", "message": f"Exception: {str(e)}"}

    async def _send_string_to_buffer(
        self, buffer_name: str, text: str
    ) -> bool:
        """Send raw string to buffer without return. Used for testing responsiveness."""
        try:
            escaped_text = text.replace('"', '\\"')
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    f"""(with-current-buffer "{buffer_name}"
                      (if (eq major-mode 'vterm-mode)
                          (vterm-send-string "{escaped_text}")
                        (progn
                          (goto-char (point-max))
                          (insert "{escaped_text}"))))""",
                ],
                capture_output=True,
                text=True,
                timeout=5,
            )

            return result.returncode == 0
        except Exception as e:
            logging.error(f"Failed to send string to buffer: {e}")
            return False

    async def send_ipdb_command(
        self, buffer_name: str, command: str
    ) -> Dict[str, Any]:
        """Send debugging commands to IPDB."""
        try:
            # Send IPDB command to vterm buffer
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    f"""(with-current-buffer "{buffer_name}"
                      (if (eq major-mode 'vterm-mode)
                          (progn
                            (vterm-send-string "{command}")
                            (vterm-send-return)
                            "ipdb-command-sent")
                        "not-vterm-buffer"))""",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                return {
                    "status": "success",
                    "buffer_name": buffer_name,
                    "command": command,
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to send IPDB command",
                }
        except Exception as e:
            return {"status": "error", "message": f"Exception: {str(e)}"}

    async def get_buffer_output(
        self, buffer_name: str, lines: int = 20
    ) -> Dict[str, Any]:
        """Retrieve recent output from buffer."""
        try:
            result = subprocess.run(
                [
                    "emacsclient",
                    "--socket-name=/home/ywatanabe/.emacs.d/server/server",
                    "--eval",
                    f"""(with-current-buffer "{buffer_name}"
                      (let ((end (point-max))
                            (start (save-excursion
                                     (goto-char (point-max))
                                     (forward-line -{lines})
                                     (point))))
                        (buffer-substring-no-properties start end)))""",
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode == 0:
                output = result.stdout.strip().strip('"')
                return {
                    "status": "success",
                    "buffer_name": buffer_name,
                    "output": output,
                    "lines_retrieved": lines,
                }
            else:
                return {
                    "status": "error",
                    "message": "Failed to get buffer output",
                }
        except Exception as e:
            return {"status": "error", "message": f"Exception: {str(e)}"}

    async def get_current_state(self, buffer_name: str) -> Dict[str, Any]:
        """Get current variables and execution state."""
        # First get buffer output to analyze
        output_result = await self.get_buffer_output(buffer_name, 50)
        if output_result["status"] != "success":
            return output_result

        # Analyze the output to extract current state
        output = output_result["output"]

        # Look for iPython prompts and current namespace
        ipython_prompt = re.search(r"In \[(\d+)\]:", output)
        current_input = (
            ipython_prompt.group(1) if ipython_prompt else "unknown"
        )

        # Look for error messages
        has_error = "Traceback" in output or "Error:" in output

        state = "error" if has_error else "idle"

        return {
            "status": "success",
            "buffer_name": buffer_name,
            "execution_state": state,
            "current_input_number": current_input,
            "recent_output": output[-500:],  # Last 500 chars
            "has_error": has_error,
        }

    # Legacy methods (adapted for backward compatibility with buffer discovery)
    async def create_session(
        self, name: str, config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Legacy method: Now returns discovered buffers instead of creating new sessions."""
        # Instead of creating, return discovered iPython buffers
        discovered = await self.find_ipython_buffers()

        if discovered:
            return {
                "status": "success",
                "message": f"Found existing iPython sessions: {[d.get('name', 'unknown') for d in discovered]}",
                "discovered_buffers": discovered,
                "note": "Buffer discovery mode: use find_ipython_buffers() instead of create_session()",
            }
        else:
            return {
                "status": "info",
                "message": "No existing iPython sessions found. Start iPython in Emacs first.",
                "suggestion": "Open Emacs, run iPython in vterm, then use find_ipython_buffers()",
            }

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """Legacy method: Now returns discovered buffers."""
        # Return discovered buffers and contexts
        ipython_buffers = await self.find_ipython_buffers()
        ipdb_sessions = await self.find_ipdb_sessions()

        return {
            "ipython_buffers": ipython_buffers,
            "ipdb_sessions": ipdb_sessions,
            "discovered_contexts": list(self.session_contexts.keys()),
            "note": "Buffer discovery mode: showing existing sessions, not created ones",
        }

    async def get_session_info(self, name: str) -> Dict[str, Any]:
        """Legacy method: Get buffer/session information by name."""
        # Try to get current state of the named buffer
        try:
            state = await self.get_current_state(name)
            if state["status"] == "success":
                return {
                    "status": "success",
                    "buffer_name": name,
                    "current_state": state,
                    "note": "Buffer discovery mode: showing buffer state, not session config",
                }
            else:
                return {
                    "status": "error",
                    "message": f"Buffer '{name}' not accessible or not found",
                    "suggestion": "Use find_ipython_buffers() to see available buffers",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get info for '{name}': {str(e)}",
            }

    async def destroy_session(self, name: str) -> Dict[str, Any]:
        """Legacy method: Clean up discovered buffer contexts."""
        # Clean up any stored context for this buffer
        if name in self.session_contexts:
            del self.session_contexts[name]
            return {
                "status": "success",
                "message": f"Cleared context for buffer '{name}'",
                "note": "Buffer discovery mode: cleared local context, buffer still exists in Emacs",
            }
        else:
            return {
                "status": "info",
                "message": f"No local context found for '{name}'",
                "note": "Buffer discovery mode: use Emacs to close actual buffers",
            }

    # Simplified Agent Management (buffer discovery mode)
    async def add_agent_to_session(
        self, session_name: str, agent_id: str
    ) -> Dict[str, Any]:
        """Legacy method: Not applicable in buffer discovery mode."""
        return {
            "status": "info",
            "message": "Agent management not needed in buffer discovery mode",
            "note": "Agents interact directly with discovered buffers via send_code_to_ipython()",
        }

    # Code Execution Methods (adapted for buffer discovery)
    async def execute_code(
        self, session_name: str, code: str, agent_id: str
    ) -> Dict[str, Any]:
        """Legacy method: Redirect to send_code_to_ipython."""
        # Use the new buffer discovery approach
        result = await self.send_code_to_ipython(session_name, code)

        if result["status"] == "success":
            return {
                "status": "success",
                "agent_id": agent_id,
                "execution_id": str(uuid.uuid4()),
                "buffer_name": session_name,
                "method": result.get("method", "unknown"),
                "note": "Redirected to send_code_to_ipython() - buffer discovery mode",
            }
        else:
            return {
                "status": "error",
                "agent_id": agent_id,
                "message": result.get("message", "Failed to execute code"),
                "note": "Buffer discovery mode: ensure buffer exists in Emacs",
            }

    async def interrupt_execution(
        self, session_name: str, agent_id: str
    ) -> Dict[str, Any]:
        """Legacy method: Interrupt not implemented for buffer discovery."""
        return {
            "status": "info",
            "message": "Use Ctrl+C in Emacs vterm to interrupt execution",
            "note": "Buffer discovery mode: interact directly with Emacs",
        }

    async def get_execution_status(self, session_name: str) -> Dict[str, Any]:
        """Legacy method: Get execution status from buffer."""
        try:
            state = await self.get_current_state(session_name)
            return {
                "buffer_name": session_name,
                "execution_state": state.get("execution_state", "unknown"),
                "current_input_number": state.get(
                    "current_input_number", "unknown"
                ),
                "note": "Buffer discovery mode: showing buffer state",
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Cannot get status for '{session_name}': {str(e)}",
            }

    # Simplified State Management (buffer discovery mode)
    async def get_variables(
        self, session_name: str, namespace: str
    ) -> Dict[str, Any]:
        """Legacy method: Variables available through iPython buffer interaction."""
        return {
            "status": "info",
            "message": "Variables accessible through iPython buffer interaction",
            "suggestion": f"Use send_code_to_ipython('{session_name}', 'globals()') to see variables",
            "note": "Buffer discovery mode: interact with actual iPython session",
        }

    async def set_variable(
        self, session_name: str, name: str, value: Any, agent_id: str
    ) -> Dict[str, Any]:
        """Legacy method: Set variables through code execution."""
        # Convert value to string representation for code execution
        value_repr = repr(value)
        code = f"{name} = {value_repr}"

        result = await self.send_code_to_ipython(session_name, code)

        if result["status"] == "success":
            return {
                "status": "success",
                "variable_name": name,
                "agent_id": agent_id,
                "code_sent": code,
                "note": "Buffer discovery mode: variable set via send_code_to_ipython()",
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to set variable: {result.get('message', 'unknown error')}",
                "agent_id": agent_id,
            }

    async def get_namespace_info(self, session_name: str) -> Dict[str, Any]:
        """Legacy method: Get namespace info via iPython commands."""
        return {
            "status": "info",
            "message": "Namespace info available through iPython commands",
            "suggestions": [
                f"send_code_to_ipython('{session_name}', 'dir()')",
                f"send_code_to_ipython('{session_name}', 'globals().keys()')",
                f"send_code_to_ipython('{session_name}', 'locals().keys()')",
            ],
            "note": "Buffer discovery mode: query iPython session directly",
        }

    async def clear_namespace(
        self,
        session_name: str,
        scope: str,
        variables: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Legacy method: Clear namespace via iPython commands."""
        if variables:
            code = "; ".join([f"del {var}" for var in variables])
        elif scope == "all":
            code = "globals().clear(); import builtins; globals().update(vars(builtins))"
        else:
            return {"status": "error", "message": "Invalid scope or variables"}

        result = await self.send_code_to_ipython(session_name, code)

        if result["status"] == "success":
            return {
                "status": "success",
                "cleared_items": (
                    variables if variables else "all user variables"
                ),
                "code_executed": code,
                "note": "Buffer discovery mode: cleared via send_code_to_ipython()",
            }
        else:
            return {
                "status": "error",
                "message": f"Failed to clear namespace: {result.get('message', 'unknown error')}",
            }

    # Communication Methods (simplified for buffer discovery)
    async def send_message(
        self, session_name: str, from_agent: str, to_agent: str, message: str
    ) -> Dict[str, Any]:
        """Legacy method: Communication via iPython comments."""
        comment_code = f"# Message from {from_agent} to {to_agent}: {message}"
        result = await self.send_code_to_ipython(session_name, comment_code)

        if result["status"] == "success":
            return {
                "status": "success",
                "message_id": str(uuid.uuid4()),
                "timestamp": datetime.now().isoformat(),
                "note": "Buffer discovery mode: message sent as iPython comment",
            }
        else:
            return {
                "status": "error",
                "message": "Failed to send message to buffer",
            }

    async def broadcast_message(
        self, session_name: str, from_agent: str, message: str
    ) -> Dict[str, Any]:
        """Legacy method: Broadcast via iPython comment."""
        comment_code = f"# Broadcast from {from_agent}: {message}"
        result = await self.send_code_to_ipython(session_name, comment_code)

        if result["status"] == "success":
            return {
                "status": "success",
                "message_id": str(uuid.uuid4()),
                "recipients": ["buffer_viewers"],
                "note": "Buffer discovery mode: broadcast sent as iPython comment",
            }
        else:
            return {
                "status": "error",
                "message": "Failed to broadcast to buffer",
            }

    async def get_agent_list(self, session_name: str) -> List[Dict[str, Any]]:
        """Legacy method: Agent list not applicable in buffer discovery."""
        return [
            {
                "note": "Buffer discovery mode: agents interact directly with discovered buffers",
                "suggestion": "Use find_ipython_buffers() to see available interaction points",
            }
        ]

    async def get_message_history(
        self, session_name: str, limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Legacy method: Message history via buffer output."""
        output_result = await self.get_buffer_output(session_name, limit or 50)

        if output_result["status"] == "success":
            return [
                {
                    "type": "buffer_output",
                    "content": output_result["output"],
                    "timestamp": datetime.now().isoformat(),
                    "note": "Buffer discovery mode: showing buffer output as message history",
                }
            ]
        else:
            return [
                {
                    "status": "error",
                    "message": "Could not retrieve buffer output",
                }
            ]

    def setup_handlers(self):
        """Set up MCP protocol handlers."""

        @self.server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """List available buffer discovery and interaction tools."""
            return [
                types.Tool(
                    name="list_ipython_sessions",
                    description="List all iPython sessions with detailed info (busy/idle, project, pwd)",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                types.Tool(
                    name="prompt_session_selection",
                    description="Show formatted session list with selection IDs for easy user choice",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                types.Tool(
                    name="select_session_by_id",
                    description="Select a specific session by ID for subsequent operations",
                    inputSchema={
                        "type": "object",
                        "properties": {"session_id": {"type": "integer"}},
                        "required": ["session_id"],
                    },
                ),
                types.Tool(
                    name="get_selected_session",
                    description="Get currently selected session information",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                types.Tool(
                    name="find_ipython_buffers",
                    description="Basic discovery of active iPython sessions in Emacs buffers",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                types.Tool(
                    name="find_ipdb_sessions",
                    description="Locate active IPDB debugging sessions in vterm",
                    inputSchema={
                        "type": "object",
                        "properties": {},
                        "required": [],
                    },
                ),
                types.Tool(
                    name="send_code_to_ipython",
                    description="Send code to existing iPython session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "buffer_name": {"type": "string"},
                            "code": {"type": "string"},
                        },
                        "required": ["buffer_name", "code"],
                    },
                ),
                types.Tool(
                    name="send_ipdb_command",
                    description="Send debugging commands to IPDB session",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "buffer_name": {"type": "string"},
                            "command": {"type": "string"},
                        },
                        "required": ["buffer_name", "command"],
                    },
                ),
                types.Tool(
                    name="get_buffer_output",
                    description="Retrieve recent output from buffer",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "buffer_name": {"type": "string"},
                            "lines": {"type": "integer", "default": 20},
                        },
                        "required": ["buffer_name"],
                    },
                ),
                types.Tool(
                    name="get_current_state",
                    description="Get current variables and execution state",
                    inputSchema={
                        "type": "object",
                        "properties": {"buffer_name": {"type": "string"}},
                        "required": ["buffer_name"],
                    },
                ),
            ]

        @self.server.call_tool()
        async def handle_call_tool(
            name: str, arguments: dict
        ) -> list[types.TextContent]:
            """Handle tool calls."""
            try:
                if name == "list_ipython_sessions":
                    result = await self.list_ipython_sessions()
                elif name == "prompt_session_selection":
                    result = await self.prompt_session_selection()
                elif name == "select_session_by_id":
                    result = await self.select_session_by_id(
                        arguments["session_id"]
                    )
                elif name == "get_selected_session":
                    result = await self.get_selected_session()
                elif name == "find_ipython_buffers":
                    result = await self.find_ipython_buffers()
                elif name == "find_ipdb_sessions":
                    result = await self.find_ipdb_sessions()
                elif name == "send_code_to_ipython":
                    result = await self.send_code_to_ipython(
                        arguments["buffer_name"], arguments["code"]
                    )
                elif name == "send_ipdb_command":
                    result = await self.send_ipdb_command(
                        arguments["buffer_name"], arguments["command"]
                    )
                elif name == "get_buffer_output":
                    result = await self.get_buffer_output(
                        arguments["buffer_name"], arguments.get("lines", 20)
                    )
                elif name == "get_current_state":
                    result = await self.get_current_state(
                        arguments["buffer_name"]
                    )
                else:
                    result = {
                        "status": "error",
                        "message": f"Unknown tool: {name}",
                    }

                return [
                    types.TextContent(
                        type="text", text=json.dumps(result, indent=2)
                    )
                ]

            except Exception as e:
                error_result = {
                    "status": "error",
                    "message": f"Tool execution failed: {str(e)}",
                }
                return [
                    types.TextContent(
                        type="text", text=json.dumps(error_result, indent=2)
                    )
                ]

    async def run(self, transport=None):
        """Run the MCP server."""
        if transport is None:
            from mcp.server.models import InitializationOptions
            from mcp.server.stdio import stdio_server

            async with stdio_server() as (read_stream, write_stream):
                await self.server.run(read_stream, write_stream)
        else:
            await self.server.run(*transport)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Emacs iPython MCP Server")
    parser.add_argument("--config", help="Configuration file path")
    parser.add_argument(
        "--debug", action="store_true", help="Enable debug logging"
    )

    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)

    server = EmacsIPythonServer(args.config)
    asyncio.run(server.initialize())
    asyncio.run(server.run())


if __name__ == "__main__":
    main()

# EOF
