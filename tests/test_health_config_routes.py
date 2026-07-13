"""Tests for sortarr.api.routes.health and config — health check and config routes."""

import sqlite3
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from httpx import ASGITransport, AsyncClient


def _create_test_db() -> sqlite3.Connection:
    """Create in-memory test database with required tables."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS pipelines (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            destination_playlist_id TEXT NOT NULL,
            destination_playlist_title TEXT NOT NULL,
            selector_mode TEXT NOT NULL DEFAULT 'AND',
            subscription_scope TEXT NOT NULL DEFAULT 'all',
            duration_min_seconds INTEGER NOT NULL DEFAULT 0,
            duration_max_seconds INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS subscriptions (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            channel_id TEXT NOT NULL,
            last_seen_at TEXT,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """
    )
    return con


@pytest.fixture
def mock_scheduler():
    """Mock PipelineScheduler for testing."""
    scheduler = Mock()
    next_run = datetime.now(timezone.utc) + timedelta(hours=6)
    scheduler.get_next_run_time.return_value = next_run
    return scheduler


@pytest.fixture
def app_with_state(mock_scheduler):
    """Create FastAPI app with test state."""
    from sortarr.api.app import AppState, create_app
    from sortarr.config import Settings
    from sortarr.db import connection

    app = create_app()
    state = AppState()
    state.settings = Settings()
    state.scheduler = mock_scheduler
    state.youtube_client = Mock()  # Authenticated
    app.state.sortarr = state

    # Set up test database connection
    connection._connection = _create_test_db()

    return app


@pytest.fixture
def app_unauthenticated(mock_scheduler):
    """Create FastAPI app with unauthenticated state."""
    from sortarr.api.app import AppState, create_app
    from sortarr.config import Settings
    from sortarr.db import connection

    app = create_app()
    state = AppState()
    state.settings = Settings()
    state.scheduler = mock_scheduler
    state.youtube_client = None  # Not authenticated
    app.state.sortarr = state

    # Set up test database connection
    connection._connection = _create_test_db()

    return app


# Health endpoint tests


@pytest.mark.asyncio
async def test_health_authenticated(app_with_state):
    """GET /health should return ok status when authenticated."""
    from sortarr.db.connection import get_connection

    conn = get_connection()

    # Insert test data
    conn.execute(
        """
        INSERT INTO pipelines (id, name, destination_playlist_id, 
                               destination_playlist_title, created_at, updated_at)
        VALUES ('p1', 'Test Pipeline', 'pl123', 'Test Playlist', 
                '2024-01-01T00:00:00Z', '2024-01-01T00:00:00Z')
    """
    )
    conn.execute(
        """
        INSERT INTO subscriptions (id, title, channel_id, created_at)
        VALUES ('s1', 'Test Channel', 'ch123', '2024-01-01T00:00:00Z')
    """
    )
    conn.execute(
        "INSERT INTO app_config (key, value) VALUES ('quota_used', '1500')"
    )
    conn.commit()

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")

    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "ok"
    assert data["authenticated"] is True
    assert data["pipelines_count"] == 1
    assert data["subscriptions_count"] == 1
    assert data["quota_used_today"] == 1500
    assert data["quota_remaining"] == 8500  # 10000 - 1500
    assert data["next_scheduled_run"] is not None


@pytest.mark.asyncio
async def test_health_unauthenticated(app_unauthenticated):
    """GET /health should return degraded status when not authenticated."""
    from sortarr.db.connection import get_connection

    conn = get_connection()
    conn.execute(
        "INSERT INTO app_config (key, value) VALUES ('quota_used', '0')"
    )
    conn.commit()

    transport = ASGITransport(app=app_unauthenticated)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")

    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "degraded"
    assert data["authenticated"] is False
    assert data["pipelines_count"] == 0
    assert data["subscriptions_count"] == 0
    assert data["quota_used_today"] == 0
    assert data["quota_remaining"] == 10000


@pytest.mark.asyncio
async def test_health_quota_remaining_never_negative(app_with_state):
    """GET /health should return 0 quota_remaining when over limit."""
    from sortarr.db.connection import get_connection

    conn = get_connection()
    conn.execute(
        "INSERT INTO app_config (key, value) VALUES ('quota_used', '12000')"
    )
    conn.commit()

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")

    assert resp.status_code == 200
    data = resp.json()

    assert data["quota_used_today"] == 12000
    assert data["quota_remaining"] == 0  # max(0, 10000 - 12000)


@pytest.mark.asyncio
async def test_health_no_scheduler(app_with_state):
    """GET /health should handle missing scheduler gracefully."""
    app_with_state.state.sortarr.scheduler = None

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/health")

    assert resp.status_code == 200
    data = resp.json()

    assert data["next_scheduled_run"] is None


# Config endpoint tests


@pytest.mark.asyncio
async def test_get_config(app_with_state):
    """GET /config should return current configuration."""
    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/config")

    assert resp.status_code == 200
    data = resp.json()

    assert data["schedule"] == "0 */6 * * *"
    assert data["reprocess_days"] == 2
    assert data["activity_limit"] == 0
    assert data["subscription_limit"] == 0
    assert data["published_after"] is None


@pytest.mark.asyncio
async def test_update_config_schedule(app_with_state, mock_scheduler):
    """PUT /config should update schedule and reschedule."""
    from sortarr.db.connection import get_connection

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            "/api/config", json={"schedule": "0 */12 * * *"}  # Every 12 hours
        )

    assert resp.status_code == 200
    data = resp.json()

    assert data["schedule"] == "0 */12 * * *"
    mock_scheduler.update_schedule.assert_called_once_with("0 */12 * * *")

    # Verify persisted to database
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM app_config WHERE key = 'schedule'"
    ).fetchone()
    assert row["value"] == "0 */12 * * *"


@pytest.mark.asyncio
async def test_update_config_reprocess_days(app_with_state):
    """PUT /config should update reprocess_days."""
    from sortarr.db.connection import get_connection

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put("/api/config", json={"reprocess_days": 5})

    assert resp.status_code == 200
    data = resp.json()

    assert data["reprocess_days"] == 5

    # Verify persisted to database
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM app_config WHERE key = 'reprocess_days'"
    ).fetchone()
    assert row["value"] == "5"


@pytest.mark.asyncio
async def test_update_config_activity_limit(app_with_state):
    """PUT /config should update activity_limit."""
    from sortarr.db.connection import get_connection

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put("/api/config", json={"activity_limit": 50})

    assert resp.status_code == 200
    data = resp.json()

    assert data["activity_limit"] == 50

    # Verify persisted to database
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM app_config WHERE key = 'activity_limit'"
    ).fetchone()
    assert row["value"] == "50"


@pytest.mark.asyncio
async def test_update_config_subscription_limit(app_with_state):
    """PUT /config should update subscription_limit."""
    from sortarr.db.connection import get_connection

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put("/api/config", json={"subscription_limit": 100})

    assert resp.status_code == 200
    data = resp.json()

    assert data["subscription_limit"] == 100

    # Verify persisted to database
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM app_config WHERE key = 'subscription_limit'"
    ).fetchone()
    assert row["value"] == "100"


@pytest.mark.asyncio
async def test_update_config_published_after(app_with_state):
    """PUT /config should update published_after."""
    from sortarr.db.connection import get_connection

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put(
            "/api/config", json={"published_after": "2024-01-01T00:00:00Z"}
        )

    assert resp.status_code == 200
    data = resp.json()

    assert data["published_after"] == "2024-01-01T00:00:00Z"

    # Verify persisted to database
    conn = get_connection()
    row = conn.execute(
        "SELECT value FROM app_config WHERE key = 'published_after'"
    ).fetchone()
    assert row["value"] == "2024-01-01T00:00:00Z"


@pytest.mark.asyncio
async def test_update_config_partial(app_with_state):
    """PUT /config should support partial updates (only non-None fields)."""
    from sortarr.db.connection import get_connection

    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Update only reprocess_days and activity_limit
        resp = await client.put(
            "/api/config", json={"reprocess_days": 7, "activity_limit": 25}
        )

    assert resp.status_code == 200
    data = resp.json()

    # Updated fields
    assert data["reprocess_days"] == 7
    assert data["activity_limit"] == 25

    # Unchanged fields
    assert data["schedule"] == "0 */6 * * *"
    assert data["subscription_limit"] == 0
    assert data["published_after"] is None


@pytest.mark.asyncio
async def test_update_config_empty_body(app_with_state):
    """PUT /config with empty body should return current config unchanged."""
    transport = ASGITransport(app=app_with_state)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.put("/api/config", json={})

    assert resp.status_code == 200
    data = resp.json()

    # All fields unchanged
    assert data["schedule"] == "0 */6 * * *"
    assert data["reprocess_days"] == 2
    assert data["activity_limit"] == 0
    assert data["subscription_limit"] == 0
    assert data["published_after"] is None
