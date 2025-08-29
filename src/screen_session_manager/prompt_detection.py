#!/usr/bin/env python3
"""Prompt detection utilities for screen session output.

Note: These are heuristics and may not work with customized prompts.
"""

import re
from typing import Optional, Tuple


def detect_prompt_state(output: str) -> Tuple[str, Optional[str]]:
    """Detect the current prompt state from captured output.
    
    Args:
        output: Captured screen output
        
    Returns:
        Tuple of (state, prompt_line) where state is one of:
        - 'shell': Shell prompt detected
        - 'python': Python REPL prompt
        - 'ipython': IPython prompt
        - 'ipdb': ipdb debugger prompt
        - 'unknown': No recognized prompt
        - 'empty': No output
        
    Note: This is a best-effort heuristic and may fail with custom prompts.
    """
    if not output:
        return 'empty', None
        
    # Get last non-empty line
    lines = output.strip().split('\n')
    last_line = None
    for line in reversed(lines):
        if line.strip():
            last_line = line
            break
            
    if not last_line:
        return 'empty', None
    
    # Check for ipdb first (most specific)
    if 'ipdb>' in last_line:
        return 'ipdb', last_line
        
    # Check for IPython
    if re.match(r'In \[\d+\]:', last_line):
        return 'ipython', last_line
        
    # Check for Python REPL
    if last_line.strip() in ('>>>', '...'):
        return 'python', last_line
        
    # Check for shell prompt (common patterns)
    # This is very heuristic - shells are highly customizable
    if any(pattern in last_line for pattern in ['$ ', '# ', '> ', '% ']):
        # Additional check: prompt usually at end of line
        if re.search(r'[$#>%]\s*$', last_line):
            return 'shell', last_line
            
    return 'unknown', last_line


def is_ready_for_input(output: str) -> bool:
    """Check if the session appears ready for input based on prompt detection.
    
    Args:
        output: Captured screen output
        
    Returns:
        True if a known prompt is detected, False otherwise
        
    Note: False negatives are common with custom prompts.
    """
    state, _ = detect_prompt_state(output)
    return state in ('shell', 'python', 'ipython', 'ipdb')


def get_prompt_wait_hint(state: str) -> str:
    """Get a hint about expected wait time for different states.
    
    Args:
        state: The detected state from detect_prompt_state
        
    Returns:
        String with timing hint
    """
    hints = {
        'shell': "Shell commands typically complete in 0.1-2 seconds",
        'python': "Python commands complete immediately unless computing",
        'ipython': "IPython commands may take longer due to magic functions",
        'ipdb': "Debugger commands complete immediately",
        'unknown': "Cannot determine timing - wait 1-2 seconds and check output",
        'empty': "No output yet - command may still be starting"
    }
    return hints.get(state, "Unknown state")