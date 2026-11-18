"""Tests for gunicorn.conf.py (production server settings)."""

import runpy
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent.parent / "gunicorn.conf.py"


def _load_config():
    """Execute the config file and return its settings as a dict."""
    return runpy.run_path(str(CONFIG_PATH))


def test_defaults_allow_concurrent_requests(monkeypatch):
    """Several threaded workers, so one chat answer cannot block the site."""
    for name in ("WEB_CONCURRENCY", "GUNICORN_THREADS", "GUNICORN_TIMEOUT"):
        monkeypatch.delenv(name, raising=False)

    config = _load_config()

    assert config["workers"] > 1
    assert config["threads"] > 1
    assert config["worker_class"] == "gthread"
    assert config["timeout"] > 30
    assert config["preload_app"] is False
    assert "bind" not in config


def test_environment_overrides(monkeypatch):
    """Hosts can tune the settings without a code change."""
    monkeypatch.setenv("WEB_CONCURRENCY", "5")
    monkeypatch.setenv("GUNICORN_THREADS", "2")
    monkeypatch.setenv("GUNICORN_TIMEOUT", "60")

    config = _load_config()

    assert (config["workers"], config["threads"], config["timeout"]) == (5, 2, 60)
