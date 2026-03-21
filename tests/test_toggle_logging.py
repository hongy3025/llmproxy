import pytest
import os
from fastapi.testclient import TestClient
from main import app
from config import config
from pathlib import Path
import shutil

@pytest.fixture
def client():
    return TestClient(app)

@pytest.fixture
def clean_logs():
    """Ensure logs directory is clean before and after tests."""
    log_dir = Path("logs/chats")
    if log_dir.exists():
        shutil.rmtree(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    yield log_dir
    # Optional: cleanup after test
    # if log_dir.exists():
    #     shutil.rmtree(log_dir)

def test_logging_disabled_by_default(client, clean_logs, mocker):
    """Test that logging is disabled by default and no files are created."""
    # Ensure config.ENABLE_CHAT_LOGS is False (default)
    mocker.patch.object(config, "ENABLE_CHAT_LOGS", False)
    
    # Mock the backend response to avoid actual network calls
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    
    # Define an async iterator for aiter_raw
    async def mock_aiter_raw():
        yield b'{"choices": [{"message": {"content": "Hello"}}]}'
        
    mock_response.aiter_raw.side_effect = mock_aiter_raw
    mock_response.aclose = mocker.AsyncMock()
    
    mocker.patch("httpx.AsyncClient.send", return_value=mock_response)
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    
    # Check that no files were created in logs/chats
    files = list(clean_logs.glob("*"))
    assert len(files) == 0, f"Expected no log files, but found: {files}"

def test_logging_enabled(client, clean_logs, mocker):
    """Test that logging is enabled and files are created when config is True."""
    # Set config.ENABLE_CHAT_LOGS to True
    mocker.patch.object(config, "ENABLE_CHAT_LOGS", True)
    
    # Mock the backend response
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    
    # Define an async iterator for aiter_raw
    async def mock_aiter_raw():
        yield b'{"choices": [{"message": {"role": "assistant", "content": "Hello there!"}}]}'
        
    mock_response.aiter_raw.side_effect = mock_aiter_raw
    mock_response.aclose = mocker.AsyncMock()
    
    mocker.patch("httpx.AsyncClient.send", return_value=mock_response)

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False
    }
    
    # We need to mock the template rendering since it might fail in test env if templates missing
    # But let's see if we can just let it run if templates exist.
    # The error "Failed to render chat text" is logged but doesn't crash the request.
    
    response = client.post("/v1/chat/completions", json=payload, headers={"X-Session-ID": "test-session"})
    assert response.status_code == 200
    
    # Check that files were created in logs/chats
    files = list(clean_logs.glob("*.yaml"))
    assert len(files) > 0, "Expected at least one .yaml log file"
    
    # Check .txt file (rendered by render_chat_text which we mocked)
    # If we want to test TXT creation, we should NOT mock render_chat_text or mock it to write a file.
    
def test_logging_toggle_via_env(mocker):
    """Test that ENABLE_CHAT_LOGS correctly reflects environment variable."""
    from config import Config
    
    # Test True
    mocker.patch.dict(os.environ, {"ENABLE_CHAT_LOGS": "True"})
    c = Config()
    assert c.ENABLE_CHAT_LOGS is True
    
    # Test False
    mocker.patch.dict(os.environ, {"ENABLE_CHAT_LOGS": "False"})
    c = Config()
    assert c.ENABLE_CHAT_LOGS is False
    
    # Test Default (False)
    mocker.patch.dict(os.environ, {})
    if "ENABLE_CHAT_LOGS" in os.environ:
        del os.environ["ENABLE_CHAT_LOGS"]
    c = Config()
    assert c.ENABLE_CHAT_LOGS is False
