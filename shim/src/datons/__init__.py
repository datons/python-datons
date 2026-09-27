"""Compatibility facade for the deprecated Datons distribution."""
import warnings
from joltio import AuthenticationError, DatonsError, QueryError, RateLimitError
from .client import Client

warnings.warn("datons is deprecated; use pip install joltio and Client().data", DeprecationWarning, stacklevel=2)
__all__ = ["Client", "AuthenticationError", "DatonsError", "QueryError", "RateLimitError"]
