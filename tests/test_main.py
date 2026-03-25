import pytest
import pytest_asyncio
import json
import httpx
from unittest.mock import patch, AsyncMock, MagicMock

from fastapi import FastAPI
from main import app, slot_manager, llama_client

@pytest_asyncio.fixture
async def test_client():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

@pytest.mark.asyncio
@patch("main.root_client.send")
@patch("main.llama_client.apply_template")
@patch("main.llama_client.tokenize")
@patch("main.slot_manager.allocate_and_prepare_slot")
async def test_chat_completions_non_stream(mock_allocate, mock_tokenize, mock_apply, mock_send, test_client):
    # Mocking llama_client and slot_manager
    mock_apply.return_value = "Mocked Prompt"
    mock_tokenize.return_value = [1, 2, 3]
    mock_allocate.return_value = 0

    # Mocking root_client.send response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.aread = AsyncMock()
    mock_response.json.return_value = {
        "content": "Mocked Response",
        "stop": True,
        "tokens_evaluated": 10,
        "tokens_predicted": 5
    }
    mock_send.return_value = mock_response

    payload = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False
    }

    response = await test_client.post("/v1/chat/completions", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "choices" in data
    assert data["choices"][0]["message"]["content"] == "Mocked Response"
    assert data["usage"]["prompt_tokens"] == 10
    assert data["usage"]["completion_tokens"] == 5

@pytest.mark.asyncio
@patch("main.root_client.send")
@patch("main.llama_client.apply_template")
@patch("main.llama_client.tokenize")
@patch("main.slot_manager.allocate_and_prepare_slot")
async def test_chat_completions_stream(mock_allocate, mock_tokenize, mock_apply, mock_send, test_client):
    # Mocking llama_client and slot_manager
    mock_apply.return_value = "Mocked Prompt"
    mock_tokenize.return_value = [1, 2, 3]
    mock_allocate.return_value = 0

    # Mocking root_client.send stream response
    mock_response = AsyncMock()
    mock_response.headers = {"Content-Type": "text/event-stream"}
    mock_response.status_code = 200
    
    async def mock_aiter_lines():
        yield 'data: {"content": "Chunk 1", "stop": false}'
        yield 'data: {"content": "Chunk 2", "stop": true}'
        yield 'data: [DONE]'
        
    mock_response.aiter_lines = mock_aiter_lines
    mock_send.return_value = mock_response

    payload = {
        "model": "test-model",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True
    }

    response = await test_client.post("/v1/chat/completions", json=payload)
    
    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
    
    content = response.text
    chunks = content.split("\n\n")
    
    # Verify mapping to standard SSE chunks
    assert "Chunk 1" in chunks[0]
    assert "Chunk 2" in chunks[1]
    assert "[DONE]" in chunks[2]
