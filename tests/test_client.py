"""Tests for the Datons client."""

import pytest

from datons import Client, DatonsError


def test_client_requires_token(monkeypatch):
    """Client raises if no token provided, env var unset, and no saved config key."""
    monkeypatch.delenv("DATONS_API_KEY", raising=False)
    # Neutralize the ~/.config/datons/config.toml fallback so the test is
    # hermetic regardless of the developer's machine.
    monkeypatch.setattr("datons.config.read_api_key", lambda: None)
    with pytest.raises(DatonsError, match="API key required"):
        Client()


def test_client_accepts_token():
    """Client initializes with explicit token."""
    client = Client(token="esd_test_abc123")
    assert client.token == "esd_test_abc123"
    assert "esd_test" in repr(client)
    client.close()


def test_client_context_manager():
    """Client works as context manager."""
    with Client(token="esd_test_abc123") as client:
        assert client.token == "esd_test_abc123"


def test_esios_manager_lazy_init():
    """EsiosDataManager is lazily initialized on first access."""
    client = Client(token="esd_test_abc123")
    assert client._esios is None
    _ = client.esios
    assert client._esios is not None
    client.close()
