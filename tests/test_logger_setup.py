import os
import shutil
from logger_setup import setup_logger
from config import config

def test_setup_logger_creates_dir(mocker, monkeypatch):
    """Test that setup_logger creates the log directory."""
    test_log_dir = "test_logs_setup"
    monkeypatch.setattr(config, "LOG_DIR", test_log_dir)
    
    mock_makedirs = mocker.patch("os.makedirs")
    mocker.patch("loguru.logger.add")
    mocker.patch("loguru.logger.remove")
    
    setup_logger()
    
    mock_makedirs.assert_called_with(test_log_dir, exist_ok=True)
