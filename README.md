<!-- ---
!-- Timestamp: 2025-08-30 09:35:45
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/screen-manager/README.md
!-- --- -->

# Screen Manager

Manage GNU Screen from Python with MCP server support.

## Install

```bash
pip install screen_manager
```

## Quick Start

```python
from screen_manager import ScreenSessionManager

manager = ScreenSessionManager()

# Create session and send commands
manager.create_session("work")
manager.send_command("work", "python script.py")
output = manager.capture("work")
```

## CLI Usage

```bash
# Create and manage sessions  
python -m screen_manager create work
python -m screen_manager send work "echo hello"
python -m screen_manager capture work

# Send multiple commands
python -m screen_manager send-commands work -c "echo 1" -c "echo 2"

# Execute files
python -m screen_manager send-file work script.py

# List and attach
python -m screen_manager list --all
python -m screen_manager attach work

# Smart create/attach  
python -m screen_manager create-or-attach work

# Cleanup
python -m screen_manager cleanup work
```

## MCP Server

```bash
# Run as MCP server
python -m screen_manager serve

# Or from Python
from screen_manager.mcp_server import main
main()
```

### MCP Configuration

Add to your MCP client configuration:

```json
{
  "mcpServers": {
    "screen-manager": {
      "command": "python",
      "args": ["-m", "screen_manager.mcp_server"],
      "description": "Manage screen sessions, send commands, and capture output"
    }
  }
}
```

## API Methods

- `create_session(name)` - Create new session
- `send_command(name, cmd)` - Send single command
- `send_commands(name, cmds)` - Send command list
- `send_command_from_file(name, file)` - Execute file
- `capture(name, lines=-1)` - Get output
- `list_sessions(all_sessions=False)` - List sessions
- `attach_session(name)` - Get attach instructions
- `create_or_attach_session(name)` - Smart create/attach
- `cleanup_session(name)` - Remove session

## MCP Tools

The MCP server provides 10 tools:
- `create_session`
- `send_command` 
- `send_commands`
- `send_command_from_file`
- `capture_output`
- `list_sessions`
- `list_all_sessions`
- `attach_session`
- `create_or_attach_session`
- `cleanup_session`

### Use Case: Debugging with selective breakpoints for concurrent debugging with multiple agents

``` python
# pip install cipdb # See https://github.com/ywatanabe1989/cipdb
manager.send_commands("debug", [
    "export CIPDB_IDS=validate,transform",
    "python script_with_cipdb.py"
])
```


## Requirements

- Python 3.8+
- `screen` command (install with `apt install screen` or `brew install screen`)


## Contact
yusuke.watanabe@scitex.ai

<!-- EOF -->