from config import Config


def test_config_defaults(monkeypatch):
    """Test that config uses defaults when no env vars are set."""
    # Clear env vars if they were set by conftest or system
    monkeypatch.delenv("BACKEND_URL", raising=False)
    monkeypatch.delenv("LISTEN_HOST", raising=False)
    monkeypatch.delenv("LISTEN_PORT", raising=False)

    # Reload Config
    cfg = Config()
    assert cfg.BACKEND_URL == "http://192.168.1.2:18085"
    assert cfg.LISTEN_HOST == "0.0.0.0"
    assert cfg.LISTEN_PORT == 8080


def test_config_from_env(monkeypatch):
    """Test that config correctly picks up environment variables."""
    monkeypatch.setenv("BACKEND_URL", "http://custom-backend/v1/")
    monkeypatch.setenv("LISTEN_HOST", "127.0.0.1")
    monkeypatch.setenv("LISTEN_PORT", "9090")

    cfg = Config()
    # Ensure trailing slash is stripped
    assert cfg.BACKEND_URL == "http://custom-backend/v1"
    assert cfg.LISTEN_HOST == "127.0.0.1"
    assert cfg.LISTEN_PORT == 9090
