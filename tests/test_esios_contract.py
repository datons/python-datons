"""HTTP contract tests for the ESIOS Python surface."""

from __future__ import annotations

from typing import Any

from datons import Client
from datons.esios.manager import EsiosDataManager
from datons.esios.models import FeedbackResult, QueryResult, SearchResult, StatusResult


class RecordingClient:
    def __init__(self) -> None:
        self.base_url = "https://api.datons.test"
        self.calls: list[tuple[str, str, dict[str, Any]]] = []
        self.responses: dict[tuple[str, str], dict[str, Any]] = {}

    def get(self, path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append(("GET", path, params or {}))
        return self.responses[("GET", path)]

    def post(self, path: str, json: dict[str, Any] | None = None) -> dict[str, Any]:
        self.calls.append(("POST", path, json or {}))
        return self.responses[("POST", path)]


def _status_payload() -> dict[str, Any]:
    return {
        "tier": "professional",
        "display_name": "Professional",
        "rate_limits": {},
        "query_limits": {},
        "restrictions": {},
        "available_tables": ["esios.indicators"],
        "getting_started": {},
        "freshness": [],
    }


def _query_payload() -> dict[str, Any]:
    return {
        "columns": [{"name": "value", "type": "Float64"}],
        "rows": [[1.5]],
        "row_count": 1,
        "query_type": "raw",
        "max_rows_applied": 50,
        "truncated": False,
    }


def test_canonical_capabilities_use_expected_methods_paths_and_bodies():
    client = RecordingClient()
    manager = EsiosDataManager(client)
    client.responses = {
        ("GET", "/esios/status"): _status_payload(),
        ("GET", "/esios/describe"): {"domains": []},
        ("POST", "/esios/search"): {"rows": [], "total": 0},
        ("POST", "/esios/query"): _query_payload(),
        ("POST", "/esios/graphql"): {"data": {"units": {"nodes": []}}},
        ("GET", "/esios/recipes"): {"recipes": [], "total": 0},
        ("POST", "/esios/recipes/capture/run"): {"recipe_id": "capture", "rows": []},
        ("GET", "/esios/knowledge"): {"knowledge": [], "total": 0},
        ("POST", "/esios/feedback"): {
            "status": "received",
            "category": "bug",
            "recorded_for": "person@example.com",
        },
    }

    assert isinstance(manager.status(), StatusResult)
    assert manager.describe("units", intent="inspect") == {"domains": []}
    assert manager.search(
        domain="units",
        facets="technology:Eólica",
        q="Aguayo",
        limit=10,
        offset=2,
        intent="find unit",
    ) == {"rows": [], "total": 0}
    assert isinstance(manager.query("SELECT 1", backend="raw"), QueryResult)
    assert manager.graphql("query Units { units { nodes { id } } }") == {
        "data": {"units": {"nodes": []}}
    }
    assert manager.recipes.list(tags=["price"]) == {"recipes": [], "total": 0}
    assert (
        manager.recipes.run("capture", params={"year": 2025})["recipe_id"] == "capture"
    )
    assert manager.knowledge.list(kind="caveat", include_content=False) == {
        "knowledge": [],
        "total": 0,
    }
    assert isinstance(
        manager.feedback.submit("bug", "wrong total", context="query", intent="audit"),
        FeedbackResult,
    )

    assert client.calls == [
        ("GET", "/esios/status", {}),
        (
            "GET",
            "/esios/describe",
            {"format": "json", "domain": "units", "intent": "inspect"},
        ),
        (
            "POST",
            "/esios/search",
            {
                "domain": "units",
                "facets": "technology:Eólica",
                "q": "Aguayo",
                "values_of": None,
                "limit": 10,
                "offset": 2,
                "intent": "find unit",
            },
        ),
        ("POST", "/esios/query", {"sql": "SELECT 1"}),
        (
            "POST",
            "/esios/graphql",
            {"query": "query Units { units { nodes { id } } }", "variables": {}},
        ),
        (
            "GET",
            "/esios/recipes",
            {"is_active": True, "view": "summary", "tags": ["price"]},
        ),
        ("POST", "/esios/recipes/capture/run", {"year": 2025}),
        ("GET", "/esios/knowledge", {"kind": "caveat", "include_content": False}),
        (
            "POST",
            "/esios/feedback",
            {
                "category": "bug",
                "message": "wrong total",
                "context": "query",
                "intent": "audit",
            },
        ),
    ]


def test_legacy_sdk_methods_keep_their_contract_on_canonical_prefix():
    client = RecordingClient()
    manager = EsiosDataManager(client)
    client.responses = {
        ("GET", "/esios/search"): {
            "query": "iber",
            "count": 0,
            "results": [],
            "offset": 0,
        },
        ("POST", "/esios/query"): _query_payload(),
    }

    assert isinstance(manager.search("iber", column="company"), SearchResult)
    assert isinstance(manager.query_raw("SELECT 1", limit=5), QueryResult)
    assert client.calls == [
        ("GET", "/esios/search", {"q": "iber", "column": "company"}),
        ("POST", "/esios/query", {"sql": "SELECT 1", "limit": 5}),
    ]


def test_client_auth_header_is_sent_for_esios_requests():
    client = Client(token="esd_test_contract", base_url="https://api.datons.test")
    try:
        assert client._http.headers["X-API-Key"] == "esd_test_contract"
        assert client.esios._client is client
    finally:
        client.close()
