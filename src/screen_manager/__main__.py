#!/usr/bin/env python3
"""
Main entry point for screen-manager.
Supports: python -m screen_manager
"""

import sys
from typing import List, Optional

from .cli import main


def main_entry(args: Optional[List[str]] = None) -> int:
    """Main entry point for the package."""
    try:
        return main(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130  # Standard exit code for Ctrl+C
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main_entry())