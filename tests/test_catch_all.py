import pytest
from httpx import AsyncClient, Response, ASGITransport
from main import app, root_client as global_root_client
import json

@pytest.mark.asyncio
async def test_catch_all_proxy(mocker):
    """Test the catch-all proxying for routes not starting with /v1."""
    # Mock backend_response with aiter_raw for StreamingResponse
    async def mock_aiter_raw():
        yield b"hello from root"

    mock_response = mocker.Mock(spec=Response)
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.aiter_raw = mock_aiter_raw
    mock_response.is_closed = False
    mock_response.aclose = mocker.AsyncMock()
    
    # Mock the global root_client.send
    mocker.patch.object(global_root_client, "send", return_value=mock_response)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/other-path")

    assert response.status_code == 200
    assert response.text == "hello from root"
