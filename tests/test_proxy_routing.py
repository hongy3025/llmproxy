import pytest
from httpx import AsyncClient, Response, ASGITransport
from main import app, client as global_client
import json

@pytest.mark.asyncio
async def test_proxy_v1_chat_completions_non_streaming(mocker):
    """Test non-streaming chat completions proxying."""
    # Mock the global client.send to return a fake response
    async def mock_aiter_raw():
        yield json.dumps({"id": "test-res", "choices": [{"text": "hi"}]}).encode()

    mock_response = mocker.Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.aiter_raw = mock_aiter_raw
    mock_response.is_closed = False
    mock_response.aclose = mocker.AsyncMock()

    mocker.patch.object(global_client, "send", return_value=mock_response)
    mocker.patch("main.log_chat_interaction") # Avoid actual logging in test

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/v1/chat/completions",
            json={"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "hello"}]},
            headers={"X-Session-ID": "test-session"}
        )

    assert response.status_code == 200
    assert response.json()["id"] == "test-res"

@pytest.mark.asyncio
async def test_proxy_v1_chat_completions_streaming(mocker):
    """Test streaming chat completions proxying."""
    # Mock the global client.send to return a streaming response
    async def mock_aiter_raw():
        yield b'data: {"choices": [{"delta": {"content": "hi"}}]}\n\n'
        yield b'data: [DONE]\n\n'

    mock_response = mocker.Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/event-stream"}
    mock_response.aiter_raw = mock_aiter_raw
    mock_response.is_closed = False
    mock_response.aclose = mocker.AsyncMock()
    
    mocker.patch.object(global_client, "send", return_value=mock_response)
    mocker.patch("main.log_chat_interaction")

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/v1/chat/completions",
            json={"model": "gpt-3.5-turbo", "stream": True, "messages": []},
            headers={"X-Session-ID": "test-session"}
        )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream"
    
    # Collect streamed content
    content = ""
    async for line in response.aiter_text():
        content += line
    
    assert "hi" in content
    assert "[DONE]" in content

@pytest.mark.asyncio
async def test_proxy_v1_models(mocker):
    """Test proxying other /v1 endpoints."""
    # Mock backend_response with aiter_raw for StreamingResponse
    async def mock_aiter_raw():
        yield json.dumps({"data": [{"id": "gpt-4"}]}).encode()

    mock_response = mocker.Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "application/json"}
    mock_response.aiter_raw = mock_aiter_raw
    mock_response.is_closed = False
    mock_response.aclose = mocker.AsyncMock()

    mocker.patch.object(global_client, "send", return_value=mock_response)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "gpt-4"
