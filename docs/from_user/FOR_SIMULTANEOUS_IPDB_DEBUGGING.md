<!-- ---
!-- Timestamp: 2025-08-29 01:24:00
!-- Author: ywatanabe
!-- File: /home/ywatanabe/proj/screen-manager/FOR_SIMULTANEOUS_IPDB_DEBUGGING.md
!-- --- -->

also, as you know adding the start trace line in scripts will stop the entire package; however, how can we allow multiple debugging agents to work on different lines in a project simultaneously?

You've hit on a critical limitation of using set_trace() - it creates a blocking breakpoint that halts the entire Python process. For multiple agents to debug different parts of a project simultaneously, we need non-blocking debugging strategies:

Solution 1: Conditional Breakpoints with Agent IDs
python
# Instead of regular set_trace(), use conditional breakpoints
import os
import ipdb

def agent_breakpoint(agent_id=None, condition=True):
    """Only break for specific agent"""
    current_agent = os.environ.get('DEBUG_AGENT_ID')
    if agent_id == current_agent and condition:
        ipdb.set_trace()
    # Otherwise, continue execution

# In code:
def process_data(items):
    for item in items:
        agent_breakpoint('agent_1', item.id == 'problematic_id')
        result = transform(item)
        agent_breakpoint('agent_2')  # Different agent debugs here
        save(result)
Solution 2: Non-Blocking Inspection Points
python
# Create inspection points instead of breakpoints
import json
import tempfile

class DebugInspector:
    @staticmethod
    def inspect(location_id, locals_dict):
        """Dump state without stopping execution"""
        output_file = f"/tmp/debug_{location_id}.json"
        with open(output_file, 'w') as f:
            json.dump({
                k: str(v) for k, v in locals_dict.items()
                if not k.startswith('__')
            }, f)
        # Continue execution normally

# Usage in code:
def process_data(items):
    for item in items:
        DebugInspector.inspect('transform_input', locals())
        result = transform(item)
        DebugInspector.inspect('transform_output', locals())
        save(result)
Solution 3: Separate Process Debugging
Each agent runs its own Python process in a different screen/tmux session:

python
# In your MCP server
@mcp.tool()
async def create_debug_session(session_name: str, script_path: str, breakpoint_line: int):
    """Each agent gets its own Python process"""
    # Create new screen session
    await create_screen_session(session_name)
    
    # Inject breakpoint at specific line
    modified_script = inject_breakpoint_at_line(script_path, breakpoint_line)
    
    # Run script in isolated session
    await send_to_session(session_name, f"python {modified_script}")
    
    return {"session": session_name, "status": "debugging"}
Solution 4: Tracing Instead of Breaking
Use Python's trace mechanism for non-blocking debugging:

python
import sys
import threading

class AgentTracer:
    def __init__(self, agent_id):
        self.agent_id = agent_id
        self.trace_data = []
        
    def trace_calls(self, frame, event, arg):
        if event == 'line':
            # Record execution without stopping
            self.trace_data.append({
                'file': frame.f_code.co_filename,
                'line': frame.f_lineno,
                'locals': frame.f_locals.copy()
            })
        return self.trace_calls
    
    def start_tracing(self, target_function):
        # Run in thread to not block
        thread = threading.Thread(
            target=self._run_with_trace, 
            args=(target_function,)
        )
        thread.start()
Solution 5: Remote Debugging with DAP (Debug Adapter Protocol)
Use debugpy for proper multi-client debugging:

python
# Each agent connects to different port
import debugpy

# Agent 1 setup
debugpy.listen(5678)  # Agent 1 port
debugpy.wait_for_client()  # Non-blocking after connection

# Agent 2 setup (different process)
debugpy.listen(5679)  # Agent 2 port
Recommended Architecture for Your Project:
python
# Enhanced BaseScreenSessionManager
class BaseScreenSessionManager:
    async def create_debug_instance(
        self, 
        agent_id: str, 
        script_path: str,
        debug_strategy: str = "subprocess"
    ):
        """Create isolated debug environment per agent"""
        
        if debug_strategy == "subprocess":
            # Each agent gets own Python subprocess
            session_name = f"debug_{agent_id}"
            await self.create_session(session_name)
            
        elif debug_strategy == "conditional":
            # Use conditional breakpoints
            os.environ['DEBUG_AGENT_ID'] = agent_id
            
        elif debug_strategy == "trace":
            # Use non-blocking tracing
            tracer = AgentTracer(agent_id)
            return tracer

    async def coordinate_agents(self, agents: List[str]):
        """Manage multiple debugging agents"""
        # Ensure agents don't interfere
        # Assign different line ranges or functions
        # Coordinate state updates
The key insight: traditional breakpoints are inherently blocking, so for true parallel debugging you need either:

Process isolation (separate Python processes per agent)
Non-blocking inspection (logging/tracing instead of breaking)
Conditional breakpoints (only one agent stops at a time)
For your MCP server, I'd recommend the separate process approach - each agent gets its own screen session running its own Python instance. This gives true parallelism and prevents interference between agents.

<!-- EOF -->