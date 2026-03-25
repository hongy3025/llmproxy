import pytest
import os
from fastapi.testclient import TestClient
from main import app
from config import config
from pathlib import Path
import shutil
import json

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

def test_logging_disabled_by_default(client, clean_logs, mocker):
    """Test that logging is disabled by default and no files are created."""
    mocker.patch.object(config, "ENABLE_CHAT_LOGS", False)
    
    # Mock dependencies for chat_completions
    mocker.patch("main.llama_client.apply_template", return_value="Mock Prompt")
    mocker.patch("main.llama_client.tokenize", return_value=[1, 2, 3])
    mocker.patch("main.slot_manager.allocate_and_prepare_slot", return_value=0)
    
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.aread = mocker.AsyncMock()
    mock_response.json.return_value = {"content": "Hello", "stop": True}
    mocker.patch("main.root_client.send", return_value=mock_response)
    
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=payload)
    assert response.status_code == 200
    
    files = list(clean_logs.glob("*"))
    assert len(files) == 0, f"Expected no log files, but found: {files}"

def test_logging_enabled(client, clean_logs, mocker):
    """Test that logging is enabled and files are created when config is True."""
    mocker.patch.object(config, "ENABLE_CHAT_LOGS", True)
    
    mocker.patch("main.llama_client.apply_template", return_value="Mock Prompt")
    mocker.patch("main.llama_client.tokenize", return_value=[1, 2, 3])
    mocker.patch("main.slot_manager.allocate_and_prepare_slot", return_value=0)
    
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.headers = {"Content-Type": "application/json"}
    mock_response.aread = mocker.AsyncMock()
    mock_response.json.return_value = {"content": "Hello there!", "stop": True}
    mocker.patch("main.root_client.send", return_value=mock_response)

    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "hi"}],
        "stream": False
    }
    
    response = client.post("/v1/chat/completions", json=payload, headers={"X-Session-ID": "test-session"})
    assert response.status_code == 200
    
    # We should have one YAML file since render_chat_text is enabled
    files = list(clean_logs.glob("*.yaml"))
    assert len(files) > 0, "Expected at least one .yaml log file"

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
