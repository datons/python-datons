"""Tests for the Datons client."""

import pytest

from datons import Client, DatonsError


def test_client_requires_token():
    """Client raises if no token provided and env var not set."""
    import os
    env_key = os.environ.pop("DATONS_API_KEY", None)
    try:
        with pytest.raises(DatonsError, match="API key required"):
            Client()
    finally:
        if env_key:
            os.environ["DATONS_API_KEY"] = env_key


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


def test_esios_data_manager_lazy_init():
    """EsiosDataManager is lazily initialized on first access."""
    client = Client(token="esd_test_abc123")
    assert client._esios_data is None
    _ = client.esios_data
    assert client._esios_data is not None
    client.close()
