import pytest
import json
import yaml
from pathlib import Path
from main import log_chat_interaction, LOG_DIR

def test_log_chat_interaction_yaml(tmp_path, mocker):
    """Test that log_chat_interaction saves interaction to a YAML file."""
    # Override LOG_DIR for testing
    mocker.patch("main.LOG_DIR", tmp_path)
    
    session_id = "test-session"
    request_data = {"method": "POST", "path": "v1/chat/completions", "body": {"prompt": "hello"}}
    response_data = {"status_code": 200, "body": {"choices": [{"text": "hi"}]}}
    timestamp = "2026-03-21_120000_000000"
    
    log_chat_interaction(session_id, request_data, response_data, timestamp)
    
    # Check if YAML file exists
    yaml_file = tmp_path / f"{timestamp}_{session_id}.yaml"
    assert yaml_file.exists()
    
    # Verify content
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    assert "chats" in data
    assert len(data["chats"]) == 1
    assert data["chats"][0]["request"] == request_data
    assert data["chats"][0]["response"] == response_data

def test_log_chat_interaction_append(tmp_path, mocker):
    """Test that log_chat_interaction appends to an existing YAML file."""
    mocker.patch("main.LOG_DIR", tmp_path)
    
    session_id = "multi-chat-session"
    timestamp = "2026-03-21_120000_000000"
    
    # First interaction
    log_chat_interaction(session_id, {"req": 1}, {"res": 1}, timestamp)
    # Second interaction (same session and timestamp)
    log_chat_interaction(session_id, {"req": 2}, {"res": 2}, timestamp)
    
    yaml_file = tmp_path / f"{timestamp}_{session_id}.yaml"
    with open(yaml_file, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    assert len(data["chats"]) == 2
    assert data["chats"][0]["request"] == {"req": 1}
    assert data["chats"][1]["request"] == {"req": 2}
