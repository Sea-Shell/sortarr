import pytest
import sqlite3
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    from sortarr.api.app import create_app
    from sortarr.db.connection import init_db as init_db_connection
    from sortarr.db.migrations import init_db

    app = create_app()
    from sortarr.api.app import AppState

    state = AppState()
    app.state.sortarr = state
    
    # Create in-memory database and initialize schema
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    
    # Initialize the global connection for repository functions
    init_db_connection(":memory:")
    
    state.db_con = conn
    return app


@pytest.mark.asyncio
async def test_health_endpoint(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_config_endpoint(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config")
    assert resp.status_code == 200
    data = resp.json()
    assert "schedule" in data
    assert "compare_distance" in data


@pytest.mark.asyncio
async def test_rules_crud(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/rules")
        assert resp.status_code == 200
        assert resp.json() == []


# ── Pipeline sort_order & reorder tests ──────────────────────────────


@pytest.mark.asyncio
async def test_create_pipeline_with_sort_order(app):
    """POST /pipelines with explicit sort_order should persist."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/api/pipelines",
            json={
                "name": "Ordered Pipeline",
                "destination_playlist_id": "PL_test",
                "sort_order": 5,
            },
        )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Ordered Pipeline"
    assert data["sort_order"] == 5


@pytest.mark.asyncio
async def test_get_pipelines_includes_sort_order(app):
    """GET /pipelines response must include sort_order field."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a pipeline first
        await client.post(
            "/api/pipelines",
            json={
                "name": "Pipe A",
                "destination_playlist_id": "PL_a",
            },
        )
        resp = await client.get("/api/pipelines")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    for p in data:
        assert "sort_order" in p
        assert isinstance(p["sort_order"], int)


@pytest.mark.asyncio
async def test_reorder_pipelines_valid(app):
    """PUT /pipelines/reorder with valid pipeline_ids reorders correctly."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create 3 pipelines
        ids = []
        for name in ["Zeta", "Alpha", "Beta"]:
            resp = await client.post(
                "/api/pipelines",
                json={"name": name, "destination_playlist_id": f"PL_{name}"},
            )
            assert resp.status_code == 201
            ids.append(resp.json()["id"])

        # Reorder: reverse the list
        reversed_ids = list(reversed(ids))
        resp = await client.put(
            "/api/pipelines/reorder",
            json={"pipeline_ids": reversed_ids},
        )
        assert resp.status_code == 204

        # Verify order in GET response
        resp = await client.get("/api/pipelines")
        assert resp.status_code == 200
        pipelines = resp.json()
        # Filter to our test pipelines and sort by sort_order
        our_pipelines = [p for p in pipelines if p["id"] in ids]
        our_pipelines.sort(key=lambda p: p["sort_order"])
        assert [p["id"] for p in our_pipelines] == reversed_ids


@pytest.mark.asyncio
async def test_reorder_pipelines_empty_list(app):
    """PUT /pipelines/reorder with empty pipeline_ids should 400."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            "/api/pipelines/reorder",
            json={"pipeline_ids": []},
        )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_reorder_pipelines_missing_field(app):
    """PUT /pipelines/reorder with missing pipeline_ids should 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            "/api/pipelines/reorder",
            json={},
        )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_reorder_pipelines_invalid_type(app):
    """PUT /pipelines/reorder with wrong type should 422."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            "/api/pipelines/reorder",
            json={"pipeline_ids": "not-a-list"},
        )
    assert resp.status_code == 422
