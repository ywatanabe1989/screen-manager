#!/usr/bin/env python3
"""Agent ID detection utilities for Claude Code integration.

Provides methods to detect terminal/session identifiers that can be used
as CLAUDE_AGENT_ID to track which agent is working in which terminal.
"""

import os
import sys
import subprocess
from typing import Optional, Dict, Any


def get_claude_agent_id() -> str:
    """Get a unique identifier for the current terminal/session.
    
    Returns a string that can be used as CLAUDE_AGENT_ID to identify
    which Claude Code agent is working in this terminal session.
    
    Priority order:
    1. Screen session (if inside screen)
    2. TMUX session (if inside tmux)  
    3. SSH TTY (if SSH session)
    4. TTY name (if available)
    5. Session ID + Terminal PID (fallback)
    
    Returns:
        String identifier suitable for CLAUDE_AGENT_ID
    """
    identifiers = get_all_identifiers()
    
    # Screen session (highest priority for our use case)
    if identifiers.get('screen'):
        return f"screen-{identifiers['screen']}"
    
    # TMUX session
    if identifiers.get('tmux'):
        tmux_id = identifiers['tmux'].split(',')[-1] if ',' in identifiers['tmux'] else identifiers['tmux']
        return f"tmux-{tmux_id}"
    
    # SSH session
    if identifiers.get('ssh_tty'):
        return f"ssh-{identifiers['ssh_tty'].replace('/', '_')}"
    
    # TTY name
    if identifiers.get('tty'):
        return f"tty-{identifiers['tty'].replace('/', '_')}"
    
    # Fallback: session + process ID
    return f"session-{identifiers['session_id']}-{identifiers['terminal_pid']}"


def get_all_identifiers() -> Dict[str, Any]:
    """Get all available terminal/session identifiers.
    
    Returns:
        Dictionary with various identifiers and their values
    """
    identifiers = {}
    
    # TTY name (if available)
    try:
        identifiers['tty'] = os.ttyname(sys.stdin.fileno())
    except (OSError, AttributeError):
        identifiers['tty'] = None
    
    # Process information
    identifiers['pid'] = os.getpid()
    identifiers['terminal_pid'] = os.getppid()  # Parent process
    identifiers['session_id'] = os.getsid(0)
    identifiers['pgid'] = os.getpgrp()
    
    # Environment variables
    identifiers['term'] = os.environ.get('TERM')
    identifiers['ssh_tty'] = os.environ.get('SSH_TTY')
    identifiers['tmux'] = os.environ.get('TMUX')
    identifiers['screen'] = os.environ.get('STY')  # Screen session
    identifiers['windowid'] = os.environ.get('WINDOWID')
    identifiers['display'] = os.environ.get('DISPLAY')
    
    # Check if already set
    identifiers['existing_claude_agent_id'] = os.environ.get('CLAUDE_AGENT_ID')
    
    return identifiers


def is_in_screen_session() -> bool:
    """Check if currently running inside a screen session."""
    return os.environ.get('STY') is not None


def is_in_tmux_session() -> bool:
    """Check if currently running inside a tmux session."""
    return os.environ.get('TMUX') is not None


def get_screen_session_name() -> Optional[str]:
    """Get the current screen session name if in screen."""
    sty = os.environ.get('STY')
    if sty:
        # STY format is usually PID.name, extract name
        if '.' in sty:
            return sty.split('.', 1)[1]
        return sty
    return None


def set_claude_agent_id_env() -> str:
    """Set CLAUDE_AGENT_ID environment variable and return the ID.
    
    Returns:
        The CLAUDE_AGENT_ID that was set
    """
    agent_id = get_claude_agent_id()
    os.environ['CLAUDE_AGENT_ID'] = agent_id
    return agent_id


def get_session_context() -> Dict[str, Any]:
    """Get comprehensive session context for logging/debugging.
    
    Returns:
        Dictionary with session context information
    """
    identifiers = get_all_identifiers()
    
    return {
        'claude_agent_id': get_claude_agent_id(),
        'in_screen': is_in_screen_session(),
        'in_tmux': is_in_tmux_session(),
        'screen_session_name': get_screen_session_name(),
        'identifiers': identifiers,
    }


def main():
    """Demo/test function."""
    print("Claude Agent ID Detection")
    print("=" * 50)
    
    # Get all identifiers
    identifiers = get_all_identifiers()
    for key, value in identifiers.items():
        print(f"{key:20}: {value}")
    
    print("\n" + "=" * 50)
    
    # Get suggested Claude Agent ID
    agent_id = get_claude_agent_id()
    print(f"CLAUDE_AGENT_ID: {agent_id}")
    
    # Show session context
    print(f"\nSession Context:")
    context = get_session_context()
    for key, value in context.items():
        if key != 'identifiers':  # Skip detailed identifiers
            print(f"  {key}: {value}")
    
    print(f"\nTo set environment variable:")
    print(f"export CLAUDE_AGENT_ID='{agent_id}'")


if __name__ == "__main__":
    main()