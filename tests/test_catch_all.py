import pytest
from httpx import AsyncClient, Response, ASGITransport
from main import app
import json

@pytest.mark.asyncio
async def test_catch_all_proxy(mocker):
    """Test the catch-all proxying for routes not starting with /v1."""
    # Mock httpx.AsyncClient as a context manager inside catch_all_request
    async def mock_aiter_raw():
        yield b"hello from root"

    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {"content-type": "text/plain"}
    mock_response.aiter_raw = mock_aiter_raw
    
    # Mock the AsyncClient instance
    mock_client_instance = mocker.Mock(spec=AsyncClient)
    mock_client_instance.build_request.return_value = mocker.Mock()
    mock_client_instance.send.return_value = mock_response
    mock_client_instance.aclose.return_value = None
    
    # Properly mock async context manager
    mock_client_instance.__aenter__ = mocker.AsyncMock(return_value=mock_client_instance)
    mock_client_instance.__aexit__ = mocker.AsyncMock(return_value=None)
    mock_client_instance.send = mocker.AsyncMock(return_value=mock_response)
    
    mocker.patch("main.httpx.AsyncClient", return_value=mock_client_instance)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/other-path")

    assert response.status_code == 200
    assert response.text == "hello from root"
