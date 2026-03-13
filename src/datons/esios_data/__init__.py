"""ESIOS Data — preprocessed Spanish electricity market data from ClickHouse."""

from datons.esios_data.manager import EsiosDataManager
from datons.esios_data.models import (
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
