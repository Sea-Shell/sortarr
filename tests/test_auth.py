"""
Tests for sortarr.core.auth — OAuth credential management.
"""

import json
import sqlite3
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from google.auth.transport.requests import AuthorizedSession
from google.oauth2.credentials import Credentials

from sortarr.core.auth import OAuthManager
from sortarr.db.connection import init_db
from sortarr.db.migrations import init_db as run_migrations


@pytest.fixture
def test_db(tmp_path: Path) -> sqlite3.Connection:
    """Create a test database with schema applied."""
    db_path = tmp_path / "test.db"
    conn = init_db(str(db_path))
    run_migrations(conn)
    return conn


@pytest.fixture
def oauth_manager(tmp_path: Path) -> OAuthManager:
    """Create an OAuthManager instance with test config."""
    client_secret = tmp_path / "client_secret.json"
    client_secret.write_text(
        json.dumps(
            {
                "installed": {
                    "client_id": "test_client_id",
                    "client_secret": "test_client_secret",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": ["http://localhost:8080/callback"],
                }
            }
        )
    )
    return OAuthManager(
        client_secret_path=str(client_secret),
        redirect_uri="http://localhost:8080/api/auth/callback",
    )


def test_save_and_load_credentials(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test save/load credentials cycle."""
    # Create test credentials
    creds = Credentials(
        token="test_access_token",
        refresh_token="test_refresh_token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client_id",
        client_secret="test_client_secret",
        scopes=["https://www.googleapis.com/auth/youtube.force-ssl"],
    )

    # Save credentials
    oauth_manager.save_credentials(creds)

    # Load credentials
    loaded = oauth_manager.get_credentials()
    assert loaded is not None
    assert loaded.token == "test_access_token"
    assert loaded.refresh_token == "test_refresh_token"
    assert loaded.token_uri == "https://oauth2.googleapis.com/token"
    assert loaded.client_id == "test_client_id"
    assert loaded.client_secret == "test_client_secret"
    assert loaded.scopes == ["https://www.googleapis.com/auth/youtube.force-ssl"]


def test_clear_credentials(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test clearing credentials from database."""
    # Save credentials
    creds = Credentials(
        token="test_token",
        refresh_token="test_refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )
    oauth_manager.save_credentials(creds)

    # Verify saved
    assert oauth_manager.is_authenticated()

    # Clear credentials
    oauth_manager.clear_credentials()

    # Verify cleared
    assert not oauth_manager.is_authenticated()
    assert oauth_manager.get_credentials() is None


def test_is_authenticated(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test is_authenticated returns correct status."""
    # Initially not authenticated
    assert not oauth_manager.is_authenticated()

    # Save credentials
    creds = Credentials(
        token="test_token",
        refresh_token="test_refresh",
        token_uri="https://oauth2.googleapis.com/token",
    )
    oauth_manager.save_credentials(creds)

    # Now authenticated
    assert oauth_manager.is_authenticated()


def test_get_http_returns_authorized_session(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test get_http returns AuthorizedSession with valid credentials."""
    # Save valid credentials
    creds = Credentials(
        token="test_token",
        refresh_token="test_refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )
    oauth_manager.save_credentials(creds)

    # Get HTTP session
    session = oauth_manager.get_http()
    assert isinstance(session, AuthorizedSession)
    assert session.credentials.token == "test_token"


def test_get_http_raises_when_not_authenticated(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test get_http raises RuntimeError when not authenticated."""
    with pytest.raises(RuntimeError, match="not authenticated"):
        oauth_manager.get_http()


def test_token_refresh_on_expired(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test token refresh logic when credentials are expired."""
    # Create expired credentials
    creds = Credentials(
        token="old_token",
        refresh_token="test_refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )
    # Mark as expired
    creds._expires_at = None  # Force expired state

    oauth_manager.save_credentials(creds)

    # Mock the refresh call
    with patch.object(Credentials, "expired", True), patch.object(
        Credentials, "refresh"
    ) as mock_refresh:
        # Mock refresh to update token
        def refresh_side_effect(request):
            creds._token = "new_token"

        mock_refresh.side_effect = refresh_side_effect

        # Get HTTP session - should trigger refresh
        oauth_manager.get_http()

        # Verify refresh was called
        mock_refresh.assert_called_once()


def test_handle_callback_saves_credentials(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test handle_callback correctly parses token response and saves."""
    mock_flow = Mock()
    mock_credentials = Credentials(
        token="callback_token",
        refresh_token="callback_refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client",
        client_secret="test_secret",
    )
    mock_flow.credentials = mock_credentials

    with patch("sortarr.core.auth.Flow.from_client_secrets_file", return_value=mock_flow):
        oauth_manager.handle_callback("test_auth_code")

    # Verify credentials were saved
    loaded = oauth_manager.get_credentials()
    assert loaded is not None
    assert loaded.token == "callback_token"
    assert loaded.refresh_token == "callback_refresh"


def test_get_authorization_url(oauth_manager: OAuthManager):
    """Test get_authorization_url generates valid URL."""
    url = oauth_manager.get_authorization_url()

    # Verify URL structure
    assert url.startswith("https://accounts.google.com/o/oauth2/auth")
    assert "client_id=test_client_id" in url
    assert "redirect_uri=" in url
    assert "scope=" in url
    assert "access_type=offline" in url


def test_credentials_never_logged(test_db: sqlite3.Connection, oauth_manager: OAuthManager, caplog):
    """Test that credentials are never logged."""
    import logging

    caplog.set_level(logging.DEBUG)

    # Save credentials with sensitive data
    creds = Credentials(
        token="SECRET_ACCESS_TOKEN",
        refresh_token="SECRET_REFRESH_TOKEN",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client",
        client_secret="SECRET_CLIENT_SECRET",
    )
    oauth_manager.save_credentials(creds)

    # Load credentials
    oauth_manager.get_credentials()

    # Get HTTP session
    oauth_manager.get_http()

    # Clear credentials
    oauth_manager.clear_credentials()

    # Check log output doesn't contain sensitive values
    log_output = caplog.text
    assert "SECRET_ACCESS_TOKEN" not in log_output
    assert "SECRET_REFRESH_TOKEN" not in log_output
    assert "SECRET_CLIENT_SECRET" not in log_output


def test_save_credentials_updates_existing(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test saving credentials updates existing row instead of creating duplicate."""
    # Save first credentials
    creds1 = Credentials(
        token="token1",
        refresh_token="refresh1",
        token_uri="https://oauth2.googleapis.com/token",
    )
    oauth_manager.save_credentials(creds1)

    # Save second credentials
    creds2 = Credentials(
        token="token2",
        refresh_token="refresh2",
        token_uri="https://oauth2.googleapis.com/token",
    )
    oauth_manager.save_credentials(creds2)

    # Verify only one row exists with latest credentials
    conn = test_db
    rows = conn.execute("SELECT COUNT(*) as count FROM oauth_credentials").fetchone()
    assert rows["count"] == 1

    loaded = oauth_manager.get_credentials()
    assert loaded.token == "token2"
    assert loaded.refresh_token == "refresh2"


def test_credentials_with_none_values(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test saving credentials with None values doesn't break JSON."""
    # Create credentials with some None values
    creds = Credentials(
        token="test_token",
        refresh_token=None,  # No refresh token
        token_uri="https://oauth2.googleapis.com/token",
    )
    oauth_manager.save_credentials(creds)

    # Load and verify
    loaded = oauth_manager.get_credentials()
    assert loaded is not None
    assert loaded.token == "test_token"
    assert loaded.refresh_token is None


def test_migrate_from_pickle_success(test_db: sqlite3.Connection, oauth_manager: OAuthManager, tmp_path):
    """Test successful migration from pickle file."""
    import pickle
    
    # Create a pickle file with credentials
    pickle_path = tmp_path / "credentials.pickle"
    creds = Credentials(
        token="pickled_token",
        refresh_token="pickled_refresh",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="client123",
        client_secret="secret456"
    )
    with open(pickle_path, "wb") as f:
        pickle.dump(creds, f)
    
    # Migrate
    result = oauth_manager.migrate_from_pickle(str(pickle_path))
    assert result is True
    
    # Verify credentials are in DB
    loaded = oauth_manager.get_credentials()
    assert loaded is not None
    assert loaded.token == "pickled_token"
    assert loaded.refresh_token == "pickled_refresh"


def test_migrate_from_pickle_no_file(test_db: sqlite3.Connection, oauth_manager: OAuthManager):
    """Test migration returns False when pickle file doesn't exist."""
    result = oauth_manager.migrate_from_pickle("nonexistent.pickle")
    assert result is False
    assert not oauth_manager.is_authenticated()


def test_migrate_from_pickle_skip_if_authenticated(test_db: sqlite3.Connection, oauth_manager: OAuthManager, tmp_path):
    """Test migration skips if DB already has credentials."""
    import pickle
    
    # Save credentials to DB first
    db_creds = Credentials(
        token="db_token",
        refresh_token="db_refresh",
        token_uri="https://oauth2.googleapis.com/token"
    )
    oauth_manager.save_credentials(db_creds)
    
    # Create pickle file
    pickle_path = tmp_path / "credentials.pickle"
    pickle_creds = Credentials(
        token="pickle_token",
        refresh_token="pickle_refresh",
        token_uri="https://oauth2.googleapis.com/token"
    )
    with open(pickle_path, "wb") as f:
        pickle.dump(pickle_creds, f)
    
    # Attempt migration
    result = oauth_manager.migrate_from_pickle(str(pickle_path))
    assert result is False
    
    # Verify DB credentials unchanged
    loaded = oauth_manager.get_credentials()
    assert loaded is not None
    assert loaded.token == "db_token"


def test_migrate_from_pickle_corrupt_file(test_db: sqlite3.Connection, oauth_manager: OAuthManager, tmp_path, caplog):
    """Test migration handles corrupt pickle file gracefully."""
    import logging
    
    # Create corrupt pickle file
    pickle_path = tmp_path / "corrupt.pickle"
    with open(pickle_path, "wb") as f:
        f.write(b"not a valid pickle")
    
    with caplog.at_level(logging.ERROR):
        result = oauth_manager.migrate_from_pickle(str(pickle_path))
    
    assert result is False
    assert "failed to migrate credentials" in caplog.text
    assert not oauth_manager.is_authenticated()


