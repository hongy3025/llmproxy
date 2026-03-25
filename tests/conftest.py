import pytest
import os
import sys

# Add src to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))


@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Set default test environment variables."""
    monkeypatch.setenv("BACKEND_URL", "http://test-backend/v1")
    monkeypatch.setenv("LISTEN_HOST", "127.0.0.1")
    monkeypatch.setenv("LISTEN_PORT", "8081")
    monkeypatch.setenv("LOG_DIR", "test_logs")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
