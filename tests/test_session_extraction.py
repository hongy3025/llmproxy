import pytest
from fastapi import Request

from utils import extract_session_id


@pytest.mark.asyncio
async def test_extract_session_id_from_header():
    """Test session ID extraction from X-Session-ID header."""
    scope = {"type": "http", "headers": [(b"x-session-id", b"header-session")]}
    request = Request(scope=scope)
    session_id = await extract_session_id(request)
    assert session_id == "header-session"


@pytest.mark.asyncio
async def test_extract_session_id_from_open_session_header():
    """Test session ID extraction from X-Open-Session header."""
    scope = {"type": "http", "headers": [(b"x-opencode-session", b"open-session-id")]}
    request = Request(scope=scope)
    session_id = await extract_session_id(request)
    assert session_id == "open-session-id"


@pytest.mark.asyncio
async def test_extract_session_id_fallback_empty():
    """Test session ID extraction fallback to empty string."""
    scope = {"type": "http", "headers": []}
    request = Request(scope=scope)
    session_id = await extract_session_id(request)
    assert session_id == ""
