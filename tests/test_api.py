import pytest
import sqlite3
from httpx import ASGITransport, AsyncClient


@pytest.fixture
def app():
    from sortarr.api.app import create_app

    app = create_app()
    from sortarr.api.app import AppState

    state = AppState()
    app.state.sortarr = state
    state.db_con = sqlite3.connect(":memory:")
    state.db_con.row_factory = sqlite3.Row
    state.db_con.executescript("""
        CREATE TABLE IF NOT EXISTS videos (
            videoId TEXT NOT NULL PRIMARY KEY,
            timestamp TEXT,
            title TEXT,
            subscriptionId TEXT,
            playlistId TEXT,
            duration_seconds INTEGER,
            route_rule TEXT
        );
        CREATE TABLE IF NOT EXISTS channel (
            id TEXT NOT NULL PRIMARY KEY,
            title TEXT
        );
        CREATE TABLE IF NOT EXISTS playlist (
            id TEXT NOT NULL PRIMARY KEY,
            title TEXT
        );
        CREATE TABLE IF NOT EXISTS subscription (
            id TEXT NOT NULL PRIMARY KEY,
            title TEXT,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS last_run (
            id NUMBER NOT NULL PRIMARY KEY,
            timestamp TEXT
        );
        CREATE TABLE IF NOT EXISTS routing_rules (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            priority INTEGER NOT NULL DEFAULT 0,
            field TEXT,
            operator TEXT NOT NULL DEFAULT 'contains',
            pattern TEXT,
            destination_playlist_id TEXT NOT NULL,
            destination_playlist_title TEXT,
            enabled INTEGER NOT NULL DEFAULT 1,
            minimum_length TEXT NOT NULL DEFAULT '0s',
            maximum_length TEXT NOT NULL DEFAULT '0s',
            catch_all INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pipeline_runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            started_at TEXT NOT NULL,
            finished_at TEXT,
            status TEXT NOT NULL DEFAULT 'running',
            subscriptions_processed INTEGER DEFAULT 0,
            subscriptions_skipped INTEGER DEFAULT 0,
            videos_added INTEGER DEFAULT 0,
            videos_skipped INTEGER DEFAULT 0,
            errors INTEGER DEFAULT 0,
            error_message TEXT,
            trigger TEXT DEFAULT 'scheduled'
        );
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pipelines (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            selector_mode TEXT NOT NULL DEFAULT 'AND',
            duration_min_seconds INTEGER NOT NULL DEFAULT 0,
            duration_max_seconds INTEGER NOT NULL DEFAULT 0,
            check_db_exists INTEGER NOT NULL DEFAULT 0,
            check_title_similarity INTEGER NOT NULL DEFAULT 0,
            compare_distance INTEGER NOT NULL DEFAULT 80,
            subscription_scope TEXT NOT NULL DEFAULT 'all',
            destination_playlist_id TEXT NOT NULL,
            destination_playlist_title TEXT NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pipeline_selectors (
            id TEXT PRIMARY KEY,
            pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
            field TEXT NOT NULL,
            operator TEXT NOT NULL,
            pattern TEXT NOT NULL,
            combine_operator TEXT NOT NULL DEFAULT 'AND',
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS pipeline_subscriptions (
            pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
            subscription_id TEXT NOT NULL,
            PRIMARY KEY (pipeline_id, subscription_id)
        );
        CREATE TABLE IF NOT EXISTS pipeline_ignore_lists (
            pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
            ignore_list_id TEXT NOT NULL,
            PRIMARY KEY (pipeline_id, ignore_list_id)
        );
    """)
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
