<!-- ---
!-- Timestamp: 2025-08-30 09:24:27
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/screen-session-manager/CIPDB_AND_SCREEN_MANAGER_DEBUGGING.md
!-- --- -->

# CIPDB and Screen Session Manager Debugging

Summary of testing conditional iPDB (cipdb) with the screen-manager MCP server.

## Overview

The screen-manager MCP server provides excellent support for interactive Python debugging sessions using cipdb (conditional iPDB). This combination enables powerful debugging workflows with session isolation and output capture.

## What is cipdb?

cipdb is a conditional debugging library that extends iPDB with:
- **ID-based breakpoints**: `cipdb.set_trace(id="validate")`
- **Environmental control**: `CIPDB_IDS=validate,save python script.py`
- **Boolean conditions**: `cipdb.set_trace(user == 'admin')`
- **Global control**: `cipdb.disable()` or `CIPDB=false`
- **Production safety**: Automatic disable in production environments

## Test Results with Screen Session Manager

### ✅ Session Management
- Successfully created isolated debugging sessions
- Proper working directory control (`/home/ywatanabe/proj/screen-manager`)
- Clean session lifecycle (create → debug → cleanup)

### ✅ Interactive Debugging Commands
Tested and verified all major ipdb commands:
- **`ll`** - List source code around current line
- **`pp locals()`** - Pretty-print local variables and objects
- **`n`** - Next line (step over function calls)
- **`s`** - Step into functions
- **`c`** - Continue execution until next breakpoint
- **`w`** - Show complete stack trace
- **`u`/`d`** - Navigate up/down the call stack
- **`pp <variable>`** - Inspect specific variables
- **`q`** - Quit debugger

### ✅ Advanced Debugging Scenarios
1. **Recursive function debugging**: Successfully stepped through factorial calculations
2. **Loop breakpoints**: Hit conditional breakpoints within iterations
3. **Stack frame navigation**: Moved between function call levels
4. **Variable scope inspection**: Examined variables at different stack levels
5. **Multi-breakpoint sessions**: Handled multiple cipdb.set_trace() calls

### ✅ Output Capture
- Complete session output captured (67 lines in test)
- Proper formatting of ipdb prompts and responses  
- Stack traces and variable dumps fully preserved
- Interactive command history maintained

## Key Advantages

### Conditional Debugging
```python
# Only debug specific conditions
cipdb.set_trace(user == 'admin', id="admin-check")

# Environment-controlled debugging  
cipdb.set_trace(os.getenv("DEBUG"), id="dev-only")

# ID-based selective debugging
cipdb.set_trace(id="critical-section")
```

### Production Safety
```bash
# Development: All breakpoints active
python script.py

# Production: All breakpoints disabled
CIPDB=false python script.py

# Selective debugging: Only specific IDs
CIPDB_IDS=validate,save python script.py
```

### Session Isolation
- Each debugging session runs in isolated screen session
- No interference between multiple debugging workflows
- Persistent sessions that survive disconnections
- Clean resource management

## Best Practices Discovered

### 1. Environment Setup
```python
# Always use project's Python environment for ipdb availability
working_dir = "/home/ywatanabe/proj/screen-manager"
```

### 2. Command Timing
```python
# Allow time for debugger to activate
delay_between_commands = 0.8  # Sufficient for most debugging commands
```

### 3. Session Management
```python
# Always clean up debugging sessions
mcp__screen-manager__cleanup_session(session_name)
```

### 4. Interactive Flow
```python
# Send debugging commands as sequential array
commands = ["ll", "pp locals()", "n", "pp variable", "c"]
```

## Debugging Workflow

1. **Create Session**: `create_session(name="debug-session", working_dir="/path")`
2. **Set Environment**: `export DEBUG=1` or `export CIPDB_IDS=specific-id`  
3. **Run Script**: `python script_with_cipdb.py`
4. **Interactive Debug**: Send ipdb commands via `send_commands()`
5. **Capture Output**: `capture_output()` to see results
6. **Clean Up**: `cleanup_session()` when done

## Production Considerations

### Safety Mechanisms
- **Environmental disable**: `CIPDB=false` disables all breakpoints
- **Global disable**: `cipdb.disable()` programmatic control
- **ID filtering**: Only specified breakpoints active in production
- **Boolean conditions**: `cipdb.set_trace(is_development_mode)`

### Performance
- Zero overhead when disabled (cipdb.set_trace(False) ≈ pass)
- Conditional evaluation only when needed
- Clean exit from debugging sessions

## Conclusion

The combination of cipdb and screen-manager provides a robust debugging environment with:
- **Full iPDB compatibility** with enhanced conditional features
- **Session isolation** preventing debugging conflicts  
- **Production safety** with multiple disable mechanisms
- **Interactive control** through MCP server commands
- **Output capture** for debugging session analysis

This setup is ideal for debugging complex Python applications, especially those with multiple agents or long-running processes where traditional debugging approaches are insufficient.

<!-- EOF -->