"""Pydantic models for ESIOS Data API responses."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ColumnInfo(BaseModel):
    """Column metadata from schema."""

    name: str
    type: str
    nullable: bool = False
    default: str | None = None
    description: str = ""


class SchemaInfo(BaseModel):
    """Table schema information."""

    table: str
    database: str
    engine: str | None = None
    columns: list[ColumnInfo]


class ProgramStats(BaseModel):
    """Per-program statistics."""

    row_count: int
    first_date: str
    last_date: str
    unique_units: int
    energy_min: float | None = None
    energy_max: float | None = None
    energy_avg: float | None = None
    price_min: float | None = None
    price_max: float | None = None
    price_avg: float | None = None
    detected_resolution: str
    columns_used: list[str]


class ProgramInfo(BaseModel):
    """Market program metadata."""

    code: str
    name: str
    description: str
    energy_source: str = ""
    price_source: str = ""
    energy_unit: str
    aggregation: str = ""
    stats: ProgramStats | None = None
    # Summary-only fields
    columns_used: list[str] = []
    row_count: int = 0
    date_range: list[str] = []


class GlobalStats(BaseModel):
    """Global dataset statistics."""

    total_rows: int
    date_min: str
    date_max: str
    unique_units: int
    unique_companies: int


class MetadataResult(BaseModel):
    """Full metadata response."""

    schema_info: SchemaInfo
    programs: list[ProgramInfo]
    global_stats: GlobalStats | None = None
    categorical_values: dict[str, list[str]] = {}


class QueryColumn(BaseModel):
    """Column in a query result."""

    name: str
    type: str


class QueryResult(BaseModel):
    """SQL query result."""

    columns: list[QueryColumn]
    rows: list[list]
    row_count: int
    query_type: str
    max_rows_applied: int
    truncated: bool


class SearchResult(BaseModel):
    """Search response.

    Shape as returned by the legacy indicator-only ``GET /esios/search`` endpoint:
    ``{query, count, results, hints, offset}``. ``results`` is a list of
    matching records (dimension rows or domain-catalog entries depending on
    the params sent).
    """

    query: str
    count: int = 0
    results: list[dict] = Field(default_factory=list)
    hints: list[str] | None = None
    offset: int = 0


class DimensionResult(BaseModel):
    """Dimension lookup response."""

    dimension: str = ""
    detail: str = ""
    count: int = 0
    values: list[str] = Field(default_factory=list)
    records: list[dict] = Field(default_factory=list)


class StatusResult(BaseModel):
    """Authenticated access tier and query limits."""

    model_config = ConfigDict(extra="allow")

    tier: str
    display_name: str
    rate_limits: dict[str, Any]
    query_limits: dict[str, Any]
    restrictions: dict[str, Any]
    available_tables: list[str]
    getting_started: dict[str, Any]
    freshness: list[dict[str, Any]] = Field(default_factory=list)


class FeedbackResult(BaseModel):
    """Acknowledgement returned by the shared feedback sink."""

    status: str
    category: str
    recorded_for: str | None = None
    detail: str | None = None
