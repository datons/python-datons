"""ESIOS Data — preprocessed Spanish electricity market data from ClickHouse."""

from datons.esios.manager import EsiosDataManager
from datons.esios.models import (
    ColumnInfo,
    DimensionResult,
    MetadataResult,
    ProgramInfo,
    QueryResult,
    SearchResult,
)

__all__ = [
    "EsiosDataManager",
    "ColumnInfo",
    "DimensionResult",
    "MetadataResult",
    "ProgramInfo",
    "QueryResult",
    "SearchResult",
]
