"""Datons — Python client for Datons data APIs."""

from datons.client import Client
from datons.exceptions import (
    AuthenticationError,
    DatonsError,
    QueryError,
    RateLimitError,
)

__all__ = [
    "Client",
    "AuthenticationError",
    "DatonsError",
    "QueryError",
    "RateLimitError",
]
