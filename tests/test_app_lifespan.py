"""Tests for FastAPI app lifespan and dependency injection."""

import sqlite3
from unittest.mock import Mock, patch

import pytest
from fastapi.testclient import TestClient

from sortarr.api.app import AppState, create_app


@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    settings = Mock()
    settings.database_file = ":memory:"
    settings.schedule = "0 */6 * * *"
    settings.public_url = "http://localhost:8080"
    settings.client_secret_path = "client_secret.json"
    settings.reprocess_days = 2
    settings.activity_limit = 0
    settings.subscription_limit = 0
    settings.published_after = None
    return settings


@pytest.fixture
def app_with_mocks(tmp_path, mock_settings):
    """Create app with mocked dependencies for testing."""
    with (
        patch("sortarr.api.app.load_settings", return_value=mock_settings),
        patch("sortarr.api.app.init_db") as mock_init_db,
        patch("sortarr.api.app.apply_schema"),
        patch("sortarr.api.app.reset_quota"),
        patch("sortarr.api.app.OAuthManager") as mock_oauth_class,
        patch("sortarr.api.app.PipelineScheduler") as mock_scheduler_class,
    ):
        # Setup mock connection
        conn = sqlite3.connect(":memory:")
        conn.row_factory = sqlite3.Row
        mock_init_db.return_value = conn

        # Setup mock OAuth manager
        mock_oauth = Mock()
        mock_oauth.is_authenticated.return_value = False
        mock_oauth.migrate_from_pickle.return_value = False
        mock_oauth_class.return_value = mock_oauth

        # Setup mock scheduler
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler

        app = create_app()
        yield app


@pytest.mark.asyncio
async def test_app_creation():
    """Test that create_app returns a FastAPI instance."""
    with (
        patch("sortarr.api.app.load_settings"),
        patch("sortarr.api.app.init_db"),
        patch("sortarr.api.app.apply_schema"),
        patch("sortarr.api.app.reset_quota"),
        patch("sortarr.api.app.OAuthManager"),
        patch("sortarr.api.app.PipelineScheduler"),
    ):
        app = create_app()
        assert app.title == "sortarr v2"
        assert hasattr(app.state, "sortarr")
        assert isinstance(app.state.sortarr, AppState)


def test_lifespan_initializes_database(tmp_path, mock_settings):
    """Test that lifespan initializes database and applies schema."""
    with (
        patch("sortarr.api.app.load_settings", return_value=mock_settings),
        patch("sortarr.api.app.init_db") as mock_init_db,
        patch("sortarr.api.app.apply_schema") as mock_apply_schema,
        patch("sortarr.api.app.reset_quota"),
        patch("sortarr.api.app.OAuthManager"),
        patch("sortarr.api.app.PipelineScheduler"),
        patch("sortarr.api.app.close_db"),
    ):
        conn = sqlite3.connect(":memory:")
        mock_init_db.return_value = conn

        app = create_app()
        # TestClient triggers lifespan
        with TestClient(app):
            pass

        # Verify database initialization
        mock_init_db.assert_called_once_with(":memory:")
        mock_apply_schema.assert_called_once_with(conn)


def test_lifespan_resets_quota(mock_settings):
    """Test that lifespan resets quota counter on startup."""
    with (
        patch("sortarr.api.app.load_settings", return_value=mock_settings),
        patch("sortarr.api.app.init_db"),
        patch("sortarr.api.app.apply_schema"),
        patch("sortarr.api.app.reset_quota") as mock_reset_quota,
        patch("sortarr.api.app.OAuthManager"),
        patch("sortarr.api.app.PipelineScheduler"),
        patch("sortarr.api.app.close_db"),
    ):
        app = create_app()
        with TestClient(app):
            pass

        mock_reset_quota.assert_called_once()


def test_lifespan_migrates_pickle_credentials(mock_settings):
    """Test that lifespan attempts to migrate pickle credentials."""
    with (
        patch("sortarr.api.app.load_settings", return_value=mock_settings),
        patch("sortarr.api.app.init_db"),
        patch("sortarr.api.app.apply_schema"),
        patch("sortarr.api.app.reset_quota"),
        patch("sortarr.api.app.OAuthManager") as mock_oauth_class,
        patch("sortarr.api.app.PipelineScheduler"),
        patch("sortarr.api.app.close_db"),
    ):
        mock_oauth = Mock()
        mock_oauth.is_authenticated.return_value = False
        mock_oauth.migrate_from_pickle.return_value = True
        mock_oauth_class.return_value = mock_oauth

        app = create_app()
        with TestClient(app):
            pass

        mock_oauth.migrate_from_pickle.assert_called_once_with("credentials.pickle")


def test_lifespan_starts_scheduler(mock_settings):
    """Test that lifespan starts the scheduler."""
    with (
        patch("sortarr.api.app.load_settings", return_value=mock_settings),
        patch("sortarr.api.app.init_db"),
        patch("sortarr.api.app.apply_schema"),
        patch("sortarr.api.app.reset_quota"),
        patch("sortarr.api.app.OAuthManager"),
        patch("sortarr.api.app.PipelineScheduler") as mock_scheduler_class,
        patch("sortarr.api.app.close_db"),
    ):
        mock_scheduler = Mock()
        mock_scheduler_class.return_value = mock_scheduler

        app = create_app()
        with TestClient(app):
            pass

        mock_scheduler.start.assert_called_once()
        mock_scheduler.stop.assert_called_once()


def test_lifespan_initializes_youtube_when_authenticated(mock_settings):
    """Test that YouTube client is initialized when authenticated."""
    with (
        patch("sortarr.api.app.load_settings", return_value=mock_settings),
        patch("sortarr.api.app.init_db"),
        patch("sortarr.api.app.apply_schema"),
        patch("sortarr.api.app.reset_quota"),
        patch("sortarr.api.app.OAuthManager") as mock_oauth_class,
        patch("sortarr.api.app.YouTubeAPIClient") as mock_youtube_class,
        patch("sortarr.api.app.Runner") as mock_runner_class,
        patch("sortarr.api.app.PipelineScheduler"),
        patch("sortarr.api.app.close_db"),
    ):
        mock_oauth = Mock()
        mock_oauth.is_authenticated.return_value = True
        mock_http = Mock()
        mock_oauth.get_http.return_value = mock_http
        mock_oauth.migrate_from_pickle.return_value = False
        mock_oauth_class.return_value = mock_oauth

        app = create_app()
        with TestClient(app):
            pass

        # Verify YouTube client was created
        mock_youtube_class.assert_called_once_with(mock_http)
        # Verify Runner was created
        mock_runner_class.assert_called_once()

