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


@pytest.mark.asyncio
async def test_get_agent_info_opencode_header():
    """Test identifying OpenCode from x-opencode-client header."""
    headers = [
        (b"user-agent", b"ai-sdk/openai-compatible/1.0.32"),
        (b"x-opencode-client", b"cli"),
    ]
    scope = {"type": "http", "headers": headers}
    request = Request(scope=scope)
    agent_info = get_agent_info(request)
    assert agent_info["name"] == "OpenCode"


@pytest.mark.asyncio
async def test_get_agent_info_opencode_ua():
    """Test identifying OpenCode from User-Agent (backward compatibility)."""
    ua = "OpenCode/1.2.3"
    scope = {"type": "http", "headers": [(b"user-agent", ua.encode())]}
    request = Request(scope=scope)
    agent_info = get_agent_info(request)
    assert agent_info["name"] == "OpenCode"
    assert agent_info["version"] == "1.2.3"
