#!/usr/bin/env python3
"""Test cipdb with screen-manager for agent debugging."""

import os
import cipdb

def process_data(data_type, items):
    """Process different types of data with conditional debugging."""
    
    # Debug only when processing "critical" data
    cipdb.set_trace(data_type == "critical", id="data-check")
    print(f"Processing {data_type} data with {len(items)} items")
    
    results = []
    for i, item in enumerate(items):
        # Debug only specific iterations
        cipdb.set_trace(i == 2, id=f"item-{i}")
        
        # Simulate processing
        result = item * 2
        results.append(result)
        
    # Always check results for critical data
    cipdb.set_trace(id="results")
    print(f"Processed {len(results)} items")
    return results

def main():
    """Main function with multiple debugging points."""
    print("Starting cipdb test for agents")
    
    # Check if we're in agent mode
    agent_id = os.getenv("AGENT_ID", "human")
    debug_mode = os.getenv("DEBUG", "false").lower() == "true"
    
    # Only debug for specific agent
    cipdb.set_trace(agent_id == "DebuggingAgent", id="agent-check")
    print(f"Running as agent: {agent_id}")
    print(f"Debug mode: {debug_mode}")
    
    # Process different data types
    datasets = [
        ("normal", [1, 2, 3]),
        ("critical", [10, 20, 30]),
        ("test", [100, 200])
    ]
    
    for data_type, items in datasets:
        cipdb.set_trace(id=f"process-{data_type}")
        results = process_data(data_type, items)
        print(f"Results for {data_type}: {results}\n")
    
    cipdb.set_trace(id="final")
    print("All processing complete!")

if __name__ == "__main__":
    # Example environment configurations:
    # 1. Debug all: python test_cipdb.py
    # 2. Debug specific ID: CIPDB_ID=results python test_cipdb.py
    # 3. Debug multiple: CIPDB_IDS=agent-check,results python test_cipdb.py
    # 4. Agent-specific: AGENT_ID=DebuggingAgent python test_cipdb.py
    # 5. Disable all: CIPDB=false python test_cipdb.py
    
    main()