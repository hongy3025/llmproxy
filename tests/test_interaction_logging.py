import pytest
import json
from main import log_interaction, log_stream_response
from loguru import logger
import httpx

def test_log_interaction_format(mocker):
    """Test that log_interaction logs JSON with expected structure."""
    # Patch logger.bind to capture log messages
    mock_info = mocker.patch.object(logger, "info")
    mocker.patch.object(logger, "bind", return_value=logger)
    
    session_id = "test-session"
    request_data = {"prompt": "hello"}
    response_data = "hi there"
    is_stream = False
    
    log_interaction(session_id, request_data, response_data, is_stream)
    
    # Check that info was called with a JSON string
    args, _ = mock_info.call_args
    log_msg = args[0]
    log_json = json.loads(log_msg)
    
    assert log_json["session_id"] == session_id
    assert log_json["request"] == request_data
    assert log_json["response"] == response_data
    assert log_json["is_stream"] == is_stream

@pytest.mark.asyncio
async def test_log_stream_response_aggregation(mocker):
    """Test that log_stream_response aggregates and logs stream content."""
    # Mock log_interaction to verify its call
    mock_log_interaction = mocker.patch("main.log_interaction")
    
    session_id = "stream-session"
    request_data = {"stream": True}
    
    # Mock backend_response
    async def mock_aiter_text():
        yield "chunk 1"
        yield "chunk 2"
    
    backend_response = mocker.Mock()
    backend_response.aiter_text = mock_aiter_text
    
    # Call the async generator
    chunks = []
    async for chunk in log_stream_response(session_id, request_data, backend_response):
        chunks.append(chunk)
    
    # Verify chunks yielded
    assert chunks == ["chunk 1", "chunk 2"]
    
    # Verify log_interaction called with aggregated content
    mock_log_interaction.assert_called_once_with(
        session_id, request_data, "chunk 1chunk 2", is_stream=True
    )
