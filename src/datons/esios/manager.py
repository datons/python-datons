"""ESIOS public API manager."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Literal

import polars as pl

from datons.esios.models import (
    DimensionResult,
    FeedbackResult,
    MetadataResult,
    QueryResult,
    SearchResult,
    StatusResult,
)

if TYPE_CHECKING:
    from datons.client import Client

API_PREFIX = "/esios"

Backend = Literal["polars", "pandas", "raw"]


class RecipesManager:
    """Vetted parameterized query recipes."""

    def __init__(self, client: Client):
        self._client = client

    def list(
        self,
        *,
        tags: list[str] | None = None,
        backend: str | None = None,
        is_active: bool = True,
        view: Literal["summary", "full"] = "summary",
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"is_active": is_active, "view": view}
        if tags is not None:
            params["tags"] = tags
        if backend is not None:
            params["backend"] = backend
        return self._client.get(f"{API_PREFIX}/recipes", params=params)

    def run(
        self, recipe_id: str, *, params: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        return self._client.post(
            f"{API_PREFIX}/recipes/{recipe_id}/run", json=params or {}
        )


class KnowledgeManager:
    """ESIOS caveats and sector knowledge catalog."""

    def __init__(self, client: Client):
        self._client = client

    def list(self, **filters: Any) -> dict[str, Any]:
        return self._client.get(
            f"{API_PREFIX}/knowledge",
            params={key: value for key, value in filters.items() if value is not None},
        )


class FeedbackManager:
    """User feedback submission backed by the shared server-side sink."""

    def __init__(self, client: Client):
        self._client = client

    def submit(
        self,
        category: str,
        message: str,
        *,
        context: str | None = None,
        intent: str | None = None,
    ) -> FeedbackResult:
        body = {
            "category": category,
            "message": message,
            "context": context,
            "intent": intent,
        }
        return FeedbackResult.model_validate(
            self._client.post(f"{API_PREFIX}/feedback", json=body)
        )


class EsiosDataManager:
    """Manager for ESIOS preprocessed data.

    Usage::

        from datons import Client

        client = Client(token="esd_live_...")

        # SQL query → Polars DataFrame (default)
        df = client.esios.query(
            "SELECT unit, datetime, energy FROM esios.archives_i90 "
            "WHERE program='PDBF' LIMIT 100"
        )

        # SQL query → pandas DataFrame
        df = client.esios.query("SELECT ...", backend="pandas")

        # Metadata (schema, programs, stats)
        meta = client.esios.metadata()

        # Search for dimension values
        results = client.esios.search("iberdrola")

        # Dimension lookup
        techs = client.esios.dimensions("technology")
    """

    def __init__(self, client: Client):
        self._client = client
        self.recipes = RecipesManager(client)
        self.knowledge = KnowledgeManager(client)
        self.feedback = FeedbackManager(client)

    def status(self) -> StatusResult:
        """Return the authenticated caller's tier, limits, and data windows."""
        return StatusResult.model_validate(self._client.get(f"{API_PREFIX}/status"))

    def describe(
        self,
        domain: str | None = None,
        *,
        format: Literal["json", "markdown", "toon"] = "json",
        intent: str | None = None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"format": format}
        if domain is not None:
            params["domain"] = domain
        if intent is not None:
            params["intent"] = intent
        return self._client.get(f"{API_PREFIX}/describe", params=params)

    def query(
        self,
        sql: str,
        *,
        limit: int | None = None,
        backend: Backend = "polars",
    ) -> Any:
        """Execute a read-only SQL query and return a DataFrame.

        Args:
            sql: SQL SELECT query against ``esios.archives_i90`` (per-program
                I90 dispatch) or ``esios.indicators`` (time series).
            limit: Max rows to return. Server enforces 50 for raw queries,
                10000 for aggregated queries.
            backend: DataFrame backend — ``"polars"`` (default) or ``"pandas"``.
                Pandas requires ``pip install datons[pandas]``.

        Returns:
            Polars or pandas DataFrame with the query results.

        Raises:
            QueryError: On invalid SQL, timeout, or write attempt.
        """
        body: dict = {"sql": sql}
        if limit is not None:
            body["limit"] = limit

        data = self._client.post(f"{API_PREFIX}/query", json=body)
        result = QueryResult.model_validate(data)

        if backend == "raw":
            return result
        if backend == "pandas":
            return self._to_pandas(result)
        return self._to_polars(result)

    def query_raw(self, sql: str, *, limit: int | None = None) -> QueryResult:
        """Execute a query and return the raw API response (no DataFrame conversion).

        Useful when you need metadata (query_type, truncated, max_rows_applied)
        or want to handle the data yourself.
        """
        body: dict = {"sql": sql}
        if limit is not None:
            body["limit"] = limit

        data = self._client.post(f"{API_PREFIX}/query", json=body)
        return QueryResult.model_validate(data)

    def metadata(
        self,
        *,
        lang: Literal["en", "es"] = "en",
        detail: Literal["summary", "full"] = "summary",
    ) -> MetadataResult:
        """Get dataset metadata: schema, programs, and global statistics.

        Args:
            lang: Language for column descriptions ('en' or 'es').
            detail: 'summary' for lightweight overview (~2.7K tokens),
                'full' for complete stats + categorical values (~5.7K tokens).
        """
        data = self._client.get(
            f"{API_PREFIX}/metadata",
            params={"lang": lang, "detail": detail},
        )
        return MetadataResult.model_validate(data)

    def search(
        self,
        q: str | None = None,
        *,
        domain: str | None = None,
        facets: str | None = None,
        values_of: list[str] | None = None,
        limit: int = 50,
        offset: int = 0,
        intent: str | None = None,
        column: str | None = None,
    ) -> dict[str, Any] | SearchResult:
        """Search canonical domains, or use the legacy indicator search signature."""
        canonical = (
            domain is not None
            or facets is not None
            or values_of is not None
            or intent is not None
        )
        if canonical:
            body: dict[str, Any] = {
                "domain": domain,
                "facets": facets,
                "q": q,
                "values_of": values_of,
                "limit": limit,
                "offset": offset,
                "intent": intent,
            }
            return self._client.post(f"{API_PREFIX}/search", json=body)

        if q is None:
            return self._client.post(
                f"{API_PREFIX}/search", json={"limit": limit, "offset": offset}
            )

        params: dict = {"q": q}
        if column:
            params["column"] = column

        data = self._client.get(f"{API_PREFIX}/search", params=params)
        return SearchResult.model_validate(data)

    def graphql(
        self, query: str, *, variables: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Execute a GraphQL document against the unified ESIOS schema."""
        return self._client.post(
            f"{API_PREFIX}/graphql", json={"query": query, "variables": variables or {}}
        )

    def dimensions(
        self,
        dim: Literal["unit", "company", "technology"] = "unit",
        *,
        detail: Literal["summary", "full"] = "summary",
        q: str | None = None,
    ) -> DimensionResult:
        """Get dimension values (unit registry, companies, technologies).

        Args:
            dim: Dimension to query.
            detail: 'summary' for flat list, 'full' for enriched records.
            q: Optional fuzzy filter.
        """
        params: dict = {"dim": dim, "detail": detail}
        if q:
            params["q"] = q

        data = self._client.get(f"{API_PREFIX}/dimensions", params=params)
        return DimensionResult.model_validate(data)

    def health(self) -> bool:
        """Check if the ESIOS Data API is reachable."""
        try:
            data = self._client.get(f"{API_PREFIX}/health")
            return data.get("status") == "ok"
        except Exception:
            return False

    # -- Internal helpers ------------------------------------------------------

    @staticmethod
    def _to_polars(result: QueryResult) -> pl.DataFrame:
        """Convert a QueryResult to a Polars DataFrame."""
        col_names = [c.name for c in result.columns]
        schema: dict[str, pl.DataType] = {}

        for col in result.columns:
            col_type = col.type.lower()
            if "datetime" in col_type:
                schema[col.name] = pl.Datetime("ms")
            elif "date" in col_type:
                schema[col.name] = pl.Date
            elif "float" in col_type:
                schema[col.name] = pl.Float64
            elif "int" in col_type or "uint" in col_type:
                schema[col.name] = pl.Int64
            else:
                schema[col.name] = pl.Utf8

        data = (
            dict(zip(col_names, zip(*result.rows)))
            if result.rows
            else {c: [] for c in col_names}
        )
        df = pl.DataFrame(data, schema=schema)
        return df

    @staticmethod
    def _to_pandas(result: QueryResult) -> Any:
        """Convert a QueryResult to a pandas DataFrame."""
        try:
            import pandas as pd
        except ImportError:
            raise ImportError(
                "pandas is required for backend='pandas'. "
                "Install it with: pip install datons[pandas]"
            ) from None

        col_names = [c.name for c in result.columns]
        df = pd.DataFrame(result.rows, columns=col_names)

        for col in result.columns:
            if "datetime" in col.type.lower() or "date" in col.type.lower():
                try:
                    df[col.name] = pd.to_datetime(df[col.name])
                except Exception:
                    pass

        return df

    def __repr__(self) -> str:
        return f"EsiosDataManager(base_url='{self._client.base_url}{API_PREFIX}')"
