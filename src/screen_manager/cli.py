#!/usr/bin/env python3
"""
CLI interface for Screen Session Manager

Provides comprehensive command-line access to all screen session management functionality.
"""

import argparse
import json
import sys
import time
from pathlib import Path
from typing import List, Optional

from .ScreenSessionManager import ScreenSessionManager


def create_command(args: argparse.Namespace) -> int:
    """Create a new screen session."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    result = manager.create_session(args.name, verbose=args.verbose)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            print(f"✓ Created session: {result['session_name']}")
        else:
            print(f"✗ Failed to create session: {result.get('error')}")
    
    return 0 if result.get("success") else 1


def send_command_cmd(args: argparse.Namespace) -> int:
    """Send a command to a session."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    result = manager.send_command(args.name, args.command, verbose=args.verbose)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            print(f"✓ Sent command to {args.name}: {args.command}")
        else:
            print(f"✗ Failed to send command: {result.get('error')}")
    
    return 0 if result.get("success") else 1


def send_commands_cmd(args: argparse.Namespace) -> int:
    """Send multiple commands to a session."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    # Parse commands from arguments
    commands = []
    if args.commands:
        commands.extend(args.commands)
    if args.file:
        try:
            with open(args.file, 'r') as f:
                file_commands = [line.strip() for line in f if line.strip() and not line.strip().startswith('#')]
                commands.extend(file_commands)
        except IOError as e:
            print(f"✗ Failed to read commands file: {e}")
            return 1
    
    if not commands:
        print("✗ No commands provided. Use --commands or --file")
        return 1
    
    result = manager.send_commands(
        args.name, 
        commands,
        delay_between_commands=args.delay,
        stop_on_failure=args.stop_on_failure,
        verbose=args.verbose
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            successful = result.get("successful_commands", 0)
            total = result.get("total_commands", 0)
            print(f"✓ Sent {successful}/{total} commands to {args.name}")
        else:
            print(f"✗ Failed to send commands: {result.get('error')}")
            if result.get("commands_sent"):
                print(f"  Commands sent before failure: {len(result['commands_sent'])}")
    
    return 0 if result.get("success") else 1


def send_file_cmd(args: argparse.Namespace) -> int:
    """Send commands from a file to a session."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    result = manager.send_command_from_file(
        args.name,
        args.file,
        mode=args.mode,
        delay_between_lines=args.delay,
        verbose=args.verbose
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            count = result.get("commands_count", 0)
            mode = result.get("mode", "unknown")
            print(f"✓ Executed file {args.file} in {mode} mode ({count} commands)")
        else:
            print(f"✗ Failed to execute file: {result.get('error')}")
    
    return 0 if result.get("success") else 1


def capture_command(args: argparse.Namespace) -> int:
    """Capture output from a session."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    output = manager.capture(args.name, n_lines=args.lines)
    
    if args.json:
        result = {
            "success": True,
            "output": output,
            "session_name": args.name,
            "lines_captured": len(output.split('\n')) if output else 0
        }
        print(json.dumps(result, indent=2))
    else:
        if output:
            print(f"=== Output from {args.name} (last {args.lines} lines) ===")
            print(output)
        else:
            print(f"No output captured from {args.name}")
    
    return 0


def list_command(args: argparse.Namespace) -> int:
    """List screen sessions."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    result = manager.list_sessions(all_sessions=args.all)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            sessions = result.get("sessions", [])
            scope = result.get("scope", "unknown")
            print(f"=== Screen Sessions ({scope}) ===")
            print(f"Found {len(sessions)} sessions:")
            for session in sessions:
                print(f"  - {session}")
        else:
            print(f"✗ Failed to list sessions: {result.get('error')}")
    
    return 0 if result.get("success") else 1


def attach_command(args: argparse.Namespace) -> int:
    """Get attachment instructions for a session."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    result = manager.attach_session(args.name, verbose=args.verbose)
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            print(f"=== Attach to session {args.name} ===")
            print(f"Command: {result.get('attach_command')}")
            print("\nInstructions:")
            for instruction in result.get("instructions", []):
                print(f"  • {instruction}")
        else:
            print(f"✗ Failed to get attachment info: {result.get('error')}")
    
    return 0 if result.get("success") else 1


def create_or_attach_command(args: argparse.Namespace) -> int:
    """Create or attach to a session."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    result = manager.create_or_attach_session(
        args.name,
        working_dir=args.working_dir,
        verbose=args.verbose
    )
    
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        action = result.get("action_taken", "unknown")
        if result.get("success"):
            if action == "create_new":
                print(f"✓ Created new session: {result.get('session_name', args.name)}")
            elif action == "attach_existing":
                print(f"✓ Session exists. Attach with: {result.get('attach_command')}")
        else:
            print(f"✗ Failed: {result.get('error')}")
    
    return 0 if result.get("success") else 1


def cleanup_command(args: argparse.Namespace) -> int:
    """Clean up a session."""
    manager = ScreenSessionManager(verbose=args.verbose)
    
    success = manager.cleanup_session(args.name)
    
    if args.json:
        result = {
            "success": success,
            "session_name": args.name,
            "message": f"Session {args.name} {'cleaned up' if success else 'cleanup failed'}"
        }
        print(json.dumps(result, indent=2))
    else:
        if success:
            print(f"✓ Cleaned up session: {args.name}")
        else:
            print(f"✗ Failed to clean up session: {args.name}")
    
    return 0 if success else 1


def info_command(args: argparse.Namespace) -> int:
    """Show system information."""
    import os
    import subprocess
    
    print("=== Screen Session Manager - System Information ===")
    
    # Check screen availability
    try:
        result = subprocess.run(['screen', '--version'], capture_output=True, text=True)
        print(f"Screen version: {result.stdout.strip()}")
    except FileNotFoundError:
        print("ERROR: screen command not found. Please install screen.")
        return 1
    
    # Check running sessions
    manager = ScreenSessionManager(verbose=False)
    sessions_result = manager.list_sessions(all_sessions=True)
    if sessions_result.get("success"):
        count = sessions_result.get("count", 0)
        print(f"Total screen sessions: {count}")
    
    # Environment info
    print(f"Python: {sys.version}")
    print(f"Working directory: {os.getcwd()}")
    
    return 0


def serve_command(args: argparse.Namespace) -> int:
    """Run MCP server."""
    try:
        from .mcp_server import main as mcp_main
        print("Starting Screen Session Manager MCP Server...")
        print("Press Ctrl+C to stop")
        mcp_main()
        return 0
    except KeyboardInterrupt:
        print("\nServer stopped")
        return 0
    except ImportError:
        print("✗ MCP server dependencies not available")
        return 1
    except Exception as e:
        print(f"✗ Server error: {e}")
        return 1


def main(args: Optional[List[str]] = None) -> int:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Screen Session Manager - Comprehensive screen session management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s create mysession                    # Create session
  %(prog)s send mysession "echo hello"        # Send single command  
  %(prog)s send-commands mysession -c "echo 1" -c "echo 2"  # Send multiple commands
  %(prog)s send-file mysession script.py      # Execute Python script
  %(prog)s capture mysession                  # Capture output
  %(prog)s list                               # List managed sessions
  %(prog)s list --all                         # List all screen sessions
  %(prog)s attach mysession                   # Get attachment instructions
  %(prog)s create-or-attach mysession         # Smart create/attach
  %(prog)s cleanup mysession                  # Clean up session
  %(prog)s serve                              # Run MCP server
        """
    )
    
    # Global options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--json', action='store_true',
                       help='Output results as JSON')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Create command
    create_parser = subparsers.add_parser('create', help='Create a new session')
    create_parser.add_argument('name', help='Session name')
    create_parser.set_defaults(func=create_command)
    
    # Send command
    send_parser = subparsers.add_parser('send', help='Send a command to session')
    send_parser.add_argument('name', help='Session name')
    send_parser.add_argument('command', help='Command to send')
    send_parser.set_defaults(func=send_command_cmd)
    
    # Send commands
    send_cmds_parser = subparsers.add_parser('send-commands', help='Send multiple commands')
    send_cmds_parser.add_argument('name', help='Session name')
    send_cmds_parser.add_argument('-c', '--commands', action='append', 
                                 help='Commands to send (can be used multiple times)')
    send_cmds_parser.add_argument('-f', '--file', 
                                 help='File containing commands (one per line)')
    send_cmds_parser.add_argument('--delay', type=float, default=0.1,
                                 help='Delay between commands (seconds)')
    send_cmds_parser.add_argument('--continue-on-failure', dest='stop_on_failure',
                                 action='store_false', default=True,
                                 help='Continue sending commands even if one fails')
    send_cmds_parser.set_defaults(func=send_commands_cmd)
    
    # Send file
    send_file_parser = subparsers.add_parser('send-file', help='Execute commands from file')
    send_file_parser.add_argument('name', help='Session name')
    send_file_parser.add_argument('file', help='File to execute')
    send_file_parser.add_argument('--mode', choices=['execute', 'lines', 'source'],
                                 default='execute', help='Execution mode')
    send_file_parser.add_argument('--delay', type=float, default=0.1,
                                 help='Delay between lines (for lines mode)')
    send_file_parser.set_defaults(func=send_file_cmd)
    
    # Capture command  
    capture_parser = subparsers.add_parser('capture', help='Capture session output')
    capture_parser.add_argument('name', help='Session name')
    capture_parser.add_argument('--lines', '-n', type=int, default=-1,
                               help='Number of lines to capture (-1 for all)')
    capture_parser.set_defaults(func=capture_command)
    
    # List command
    list_parser = subparsers.add_parser('list', help='List screen sessions')
    list_parser.add_argument('--all', action='store_true',
                            help='List all screen sessions (not just managed ones)')
    list_parser.set_defaults(func=list_command)
    
    # Attach command
    attach_parser = subparsers.add_parser('attach', help='Get session attachment instructions')
    attach_parser.add_argument('name', help='Session name')
    attach_parser.set_defaults(func=attach_command)
    
    # Create or attach command
    create_attach_parser = subparsers.add_parser('create-or-attach', help='Create session or get attach instructions')
    create_attach_parser.add_argument('name', help='Session name')
    create_attach_parser.add_argument('--working-dir', help='Working directory (for new sessions)')
    create_attach_parser.set_defaults(func=create_or_attach_command)
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up a session')
    cleanup_parser.add_argument('name', help='Session name')
    cleanup_parser.set_defaults(func=cleanup_command)
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show system information')
    info_parser.set_defaults(func=info_command)
    
    # Serve command (MCP server)
    serve_parser = subparsers.add_parser('serve', help='Run MCP server')
    serve_parser.set_defaults(func=serve_command)
    
    # Parse arguments
    parsed_args = parser.parse_args(args)
    
    if not hasattr(parsed_args, 'func'):
        parser.print_help()
        return 1
    
    return parsed_args.func(parsed_args)


if __name__ == "__main__":
    sys.exit(main())