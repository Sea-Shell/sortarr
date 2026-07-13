import sqlite3

import pytest
from httpx import ASGITransport, AsyncClient


def _db() -> sqlite3.Connection:
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute(
        "CREATE TABLE IF NOT EXISTS app_config (key TEXT PRIMARY KEY, value TEXT)"
    )
    return con


@pytest.mark.asyncio
async def test_auth_status_returns_503_without_oauth_manager():
    """Auth endpoints return 503 when OAuth is not configured."""
    from sortarr.api.app import AppState, create_app

    app = create_app()
    state = AppState()
    state.db_con = _db()
    # No oauth_manager set
    app.state.sortarr = state
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/status")
    assert resp.status_code == 503
    data = resp.json()
    assert "OAuth not configured" in data["detail"]


@pytest.mark.asyncio
async def test_auth_login_returns_503_without_oauth_manager():
    """Auth endpoints return 503 when OAuth is not configured."""
    from sortarr.api.app import AppState, create_app

    app = create_app()
    state = AppState()
    state.db_con = _db()
    # No oauth_manager set
    app.state.sortarr = state
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/login")
    assert resp.status_code == 503
    data = resp.json()
    assert "OAuth not configured" in data["detail"]
