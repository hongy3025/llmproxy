import json

import pytest
from httpx import ASGITransport, AsyncClient, Response

from main import app
from main import client as global_client


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

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/v1/models")

    assert response.status_code == 200
    assert response.json()["data"][0]["id"] == "gpt-4"
