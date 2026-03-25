import pytest
from fastapi import Request

from utils import get_agent_info


@pytest.mark.asyncio
async def test_get_agent_info_claude_code():
    """Test identifying Claude Code from User-Agent."""
    ua = "ClaudeCode/0.25.0 (Anthropic; +https://www.anthropic.com/claude-code)"
    scope = {"type": "http", "headers": [(b"user-agent", ua.encode())]}
    request = Request(scope=scope)
    agent_info = get_agent_info(request)
    assert agent_info["name"] == "Claude Code"
    assert agent_info["version"] == "0.25.0"
