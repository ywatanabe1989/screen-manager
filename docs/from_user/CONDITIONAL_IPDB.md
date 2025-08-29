<!-- ---
!-- Timestamp: 2025-08-29 01:19:48
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/screen-manager/cipd.md
!-- --- -->

cipdb is available on PyPI - here's a minimal implementation to get you started:
setup.py
pythonfrom setuptools import setup, find_packages

setup(
    name="cipdb",
    version="0.1.0",
    packages=find_packages(),
    install_requires=["ipdb"],
    python_requires=">=3.6",
    description="Conditional debugging with ipdb",
    long_description="Drop-in replacement for ipdb.set_trace() with conditional breakpoints based on ID or custom conditions",
    author="Your Name",
    url="https://github.com/yourusername/cipdb",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
    ],
)
cipdb/__init__.py
python"""Conditional iPDB - Conditional debugging for Python"""
import os
import ipdb as _ipdb
from typing import Optional, Union, Callable

__version__ = "0.1.0"
__all__ = ["set_trace", "post_mortem"]

# Check common environment variables for ID
def _get_active_id():
    return (
        os.getenv("CIPDB_ID") or 
        os.getenv("AGENT_ID") or 
        os.getenv("DEBUG_ID") or
        os.getenv("CLAUDE_CODE_ID")
    )

def set_trace(
    id: Optional[str] = None,
    condition: Union[bool, Callable[[], bool]] = True,
    frame=None
):
    """
    Conditional breakpoint - only activates when conditions are met.
    
    Args:
        id: Only break if this matches the active ID (from environment)
        condition: Boolean or callable that returns boolean
        frame: Stack frame (passed to ipdb.set_trace)
    
    Examples:
        cipdb.set_trace()  # Always break (like regular ipdb)
        cipdb.set_trace(id="agent_1")  # Only break for agent_1
        cipdb.set_trace(condition=lambda: x > 10)  # Break when x > 10
        cipdb.set_trace(id="test", condition=debug_mode)  # Both conditions
    """
    # Evaluate condition if it's callable
    if callable(condition):
        condition = condition()
    
    # Check ID match if specified
    if id is not None:
        active_id = _get_active_id()
        if active_id != id:
            return  # Skip breakpoint
    
    # Check condition
    if not condition:
        return  # Skip breakpoint
    
    # All conditions met - activate debugger
    if frame is None:
        _ipdb.set_trace()
    else:
        _ipdb.set_trace(frame=frame)

def post_mortem(traceback=None, id: Optional[str] = None):
    """Conditional post-mortem debugging"""
    if id is not None:
        active_id = _get_active_id()
        if active_id != id:
            return
    
    _ipdb.post_mortem(traceback)

# Convenience: make cipdb.set_trace() work
set_trace.__module__ = __name__
README.md
markdown# cipdb - Conditional iPDB

Drop-in replacement for `ipdb.set_trace()` that only activates under certain conditions.

## Installation
```bash
pip install cipdb
Usage
Basic (same as ipdb)
pythonimport cipdb
cipdb.set_trace()  # Always breaks
ID-based debugging
python# Only breaks when CIPDB_ID=agent_1 (or AGENT_ID, DEBUG_ID, CLAUDE_CODE_ID)
cipdb.set_trace(id="agent_1")
Conditional debugging
pythoncipdb.set_trace(condition=lambda: len(data) > 100)
cipdb.set_trace(condition=error_occurred)
Combined
pythoncipdb.set_trace(id="test_session", condition=x > 10)
Environment Variables
Set any of these to control which ID is active:

CIPDB_ID
AGENT_ID
DEBUG_ID
CLAUDE_CODE_ID


This minimal package:
- Takes ~30 lines of actual code
- Provides immediate value for multi-agent debugging
- Has potential for broader use cases
- Easy to extend later with more features

You could have this on PyPI within an hour, and it would solve your immediate problem while potentially helping others with similar needs.

<!-- EOF -->