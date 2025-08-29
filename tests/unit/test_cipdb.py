#!/usr/bin/env python3
"""
Placeholder test for cipdb - now redirects to standalone package integration tests.

The cipdb functionality is now provided by the standalone cipdb package.
See test_cipdb_integration.py for integration tests.
"""

import pytest


@pytest.mark.unit
class TestGetAgentId:
    """Placeholder class to satisfy smoke test expectations."""
    
    def test_get_agent_id_from_claude_agent_id(self):
        """Placeholder test that checks agent ID functionality is in screen-manager."""
        from screen_manager.mcp_server import get_agent_id
        import os
        
        # Test agent ID detection works in screen-manager
        os.environ['CLAUDE_AGENT_ID'] = 'test-agent'
        try:
            agent_id = get_agent_id()
            assert agent_id == 'test-agent'
        finally:
            del os.environ['CLAUDE_AGENT_ID']


# Note: Full cipdb testing is now in the standalone cipdb package.
# This file only tests the integration points within screen-manager.