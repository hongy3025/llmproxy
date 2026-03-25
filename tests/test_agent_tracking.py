import pytest
from fastapi import Request

from utils import extract_session_id, get_agent_info


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
async def test_extract_session_id_from_correlation_id():
    """Test extracting session ID from X-Correlation-ID."""
    scope = {
        "type": "http",
        "headers": [(b"x-correlation-id", b"stable-agent-session")],
    }
    request = Request(scope=scope)
    session_id = await extract_session_id(request)
    assert session_id == "stable-agent-session"


@pytest.mark.asyncio
async def test_extract_session_id_from_body_metadata():
    """Test session ID extraction from body metadata."""
    body_json = {"messages": [], "metadata": {"conversation_id": "meta-conv-id"}}
    scope = {"type": "http", "headers": []}
    request = Request(scope=scope)
    session_id = await extract_session_id(request, body_json)
    assert session_id == "meta-conv-id"


@pytest.mark.asyncio
async def test_extract_session_id_from_conversation_id_header():
    """Test session ID extraction from X-Conversation-ID header."""
    scope = {"type": "http", "headers": [(b"x-conversation-id", b"header-conv-id")]}
    request = Request(scope=scope)
    session_id = await extract_session_id(request)
    assert session_id == "header-conv-id"
