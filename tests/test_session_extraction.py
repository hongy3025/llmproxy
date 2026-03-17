import pytest
import uuid
from main import extract_session_id
from fastapi import Request
import json

@pytest.mark.asyncio
async def test_extract_session_id_from_header():
    """Test session ID extraction from X-Session-ID header."""
    scope = {
        "type": "http",
        "headers": [(b"x-session-id", b"header-session")]
    }
    request = Request(scope=scope)
    session_id = await extract_session_id(request)
    assert session_id == "header-session"

@pytest.mark.asyncio
async def test_extract_session_id_from_body_session_id():
    """Test session ID extraction from request body 'session_id'."""
    scope = {"type": "http", "headers": []}
    request = Request(scope=scope)
    body_json = {"session_id": "body-session-id"}
    session_id = await extract_session_id(request, body_json)
    assert session_id == "body-session-id"

@pytest.mark.asyncio
async def test_extract_session_id_from_body_user():
    """Test session ID extraction from request body 'user'."""
    scope = {"type": "http", "headers": []}
    request = Request(scope=scope)
    body_json = {"user": "user-session-id"}
    session_id = await extract_session_id(request, body_json)
    assert session_id == "user-session-id"

@pytest.mark.asyncio
async def test_extract_session_id_fallback_uuid():
    """Test session ID extraction fallback to UUID."""
    scope = {"type": "http", "headers": []}
    request = Request(scope=scope)
    session_id = await extract_session_id(request)
    
    # Check if it's a valid UUID
    try:
        uuid_obj = uuid.UUID(session_id, version=4)
        assert str(uuid_obj) == session_id
    except ValueError:
        pytest.fail(f"session_id {session_id} is not a valid UUID v4")
