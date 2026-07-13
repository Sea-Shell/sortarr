"""Tests for sortarr.api.routes.auth — OAuth authentication routes."""

import sqlite3
from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from httpx import ASGITransport, AsyncClient


def _create_test_db() -> sqlite3.Connection:
    """Create in-memory test database with oauth_credentials table."""
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.executescript(
        """
        CREATE TABLE IF NOT EXISTS oauth_credentials (
            id INTEGER PRIMARY KEY,
            token_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS app_config (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );
    """
    )
    return con


@pytest.fixture
def mock_oauth_manager():
    """Mock OAuthManager for testing."""
    manager = Mock()
    manager.is_authenticated.return_value = False
    manager.get_credentials.return_value = None
    return manager


@pytest.fixture
def app_with_oauth(mock_oauth_manager):
    """Create FastAPI app with mocked OAuth manager."""
    from sortarr.api.app import AppState, create_app

    app = create_app()
    state = AppState()
    state.db_con = _create_test_db()
    state.oauth_manager = mock_oauth_manager
    app.state.sortarr = state
    return app


# Login endpoint tests


@pytest.mark.asyncio
async def test_login_redirects_to_google(app_with_oauth, mock_oauth_manager):
    """GET /auth/login should redirect to Google OAuth consent screen."""
    mock_oauth_manager.get_authorization_url.return_value = (
        "https://accounts.google.com/o/oauth2/auth?client_id=test"
    )

    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        resp = await client.get("/api/auth/login")

    assert resp.status_code == 302
    assert (
        resp.headers["location"]
        == "https://accounts.google.com/o/oauth2/auth?client_id=test"
    )
    mock_oauth_manager.get_authorization_url.assert_called_once()


@pytest.mark.asyncio
async def test_login_returns_503_without_oauth_manager():
    """GET /auth/login should return 503 if OAuth is not configured."""
    from sortarr.api.app import AppState, create_app

    app = create_app()
    state = AppState()
    state.db_con = _create_test_db()
    # No oauth_manager set
    app.state.sortarr = state

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/login")

    assert resp.status_code == 503
    data = resp.json()
    assert "OAuth not configured" in data["detail"]


# Callback endpoint tests


@pytest.mark.asyncio
async def test_callback_exchanges_code_and_saves_credentials(
    app_with_oauth, mock_oauth_manager
):
    """GET /auth/callback?code=... should exchange code and save tokens."""
    mock_oauth_manager.handle_callback.return_value = None

    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/callback?code=test_auth_code")

    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "authentication successful"
    assert data["authenticated"] is True
    mock_oauth_manager.handle_callback.assert_called_once_with("test_auth_code")


@pytest.mark.asyncio
async def test_callback_returns_400_without_code(app_with_oauth):
    """GET /auth/callback without code parameter should return 400."""
    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/callback")

    assert resp.status_code == 422  # FastAPI validation error for missing required param


@pytest.mark.asyncio
async def test_callback_returns_500_on_oauth_error(app_with_oauth, mock_oauth_manager):
    """GET /auth/callback should return 500 if OAuth exchange fails."""
    mock_oauth_manager.handle_callback.side_effect = RuntimeError("invalid grant")

    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/callback?code=bad_code")

    assert resp.status_code == 500
    data = resp.json()
    assert "authentication failed" in data["detail"]


# Status endpoint tests


@pytest.mark.asyncio
async def test_status_returns_not_authenticated(app_with_oauth, mock_oauth_manager):
    """GET /auth/status should return authenticated=false when not logged in."""
    mock_oauth_manager.is_authenticated.return_value = False

    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is False
    assert data["expires_at"] is None


@pytest.mark.asyncio
async def test_status_returns_authenticated_with_expiry(
    app_with_oauth, mock_oauth_manager
):
    """GET /auth/status should return authenticated=true with expiry when logged in."""
    mock_oauth_manager.is_authenticated.return_value = True

    # Mock credentials with expiry
    mock_creds = Mock()
    expiry_time = datetime.now(timezone.utc) + timedelta(hours=1)
    mock_creds.expiry = expiry_time
    mock_oauth_manager.get_credentials.return_value = mock_creds

    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is True
    assert data["expires_at"] == expiry_time.isoformat()


@pytest.mark.asyncio
async def test_status_handles_missing_expiry(app_with_oauth, mock_oauth_manager):
    """GET /auth/status should handle credentials without expiry field."""
    mock_oauth_manager.is_authenticated.return_value = True

    # Mock credentials without expiry
    mock_creds = Mock()
    mock_creds.expiry = None
    mock_oauth_manager.get_credentials.return_value = mock_creds

    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/auth/status")

    assert resp.status_code == 200
    data = resp.json()
    assert data["authenticated"] is True
    assert data["expires_at"] is None


# Logout endpoint tests


@pytest.mark.asyncio
async def test_logout_clears_credentials(app_with_oauth, mock_oauth_manager):
    """POST /auth/logout should clear stored credentials."""
    mock_oauth_manager.clear_credentials.return_value = None

    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/auth/logout")

    assert resp.status_code == 200
    data = resp.json()
    assert data["message"] == "logged out successfully"
    mock_oauth_manager.clear_credentials.assert_called_once()


@pytest.mark.asyncio
async def test_logout_returns_503_without_oauth_manager():
    """POST /auth/logout should return 503 if OAuth is not configured."""
    from sortarr.api.app import AppState, create_app

    app = create_app()
    state = AppState()
    state.db_con = _create_test_db()
    # No oauth_manager set
    app.state.sortarr = state

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/auth/logout")

    assert resp.status_code == 503
    data = resp.json()
    assert "OAuth not configured" in data["detail"]


# Integration test


@pytest.mark.asyncio
async def test_full_oauth_flow_integration(app_with_oauth, mock_oauth_manager):
    """Integration test: login → callback → status → logout."""
    # Setup mocks
    mock_oauth_manager.get_authorization_url.return_value = (
        "https://accounts.google.com/o/oauth2/auth?client_id=test"
    )
    mock_oauth_manager.handle_callback.return_value = None

    transport = ASGITransport(app=app_with_oauth)
    async with AsyncClient(
        transport=transport, base_url="http://test", follow_redirects=False
    ) as client:
        # 1. Login redirects
        resp = await client.get("/api/auth/login")
        assert resp.status_code == 302

        # 2. Callback succeeds
        resp = await client.get("/api/auth/callback?code=test_code")
        assert resp.status_code == 200
        assert resp.json()["authenticated"] is True

        # 3. Status shows authenticated
        mock_oauth_manager.is_authenticated.return_value = True
        resp = await client.get("/api/auth/status")
        assert resp.status_code == 200
        assert resp.json()["authenticated"] is True

        # 4. Logout clears
        resp = await client.post("/api/auth/logout")
        assert resp.status_code == 200
        assert "logged out" in resp.json()["message"]
