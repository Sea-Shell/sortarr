"""Tests for FastAPI dependency injection."""

from unittest.mock import Mock

import pytest
from fastapi import HTTPException

from sortarr.api.app import AppState
from sortarr.api.deps import get_oauth_manager, get_runner, get_state, require_youtube


@pytest.fixture
def mock_request():
    """Create a mock FastAPI request."""
    request = Mock()
    request.app.state.sortarr = AppState()
    return request


def test_get_state(mock_request):
    """Test get_state returns app state from request."""
    state = get_state(mock_request)
    assert isinstance(state, AppState)
    assert state is mock_request.app.state.sortarr


def test_get_oauth_manager_success(mock_request):
    """Test get_oauth_manager returns OAuth manager when initialized."""
    mock_oauth = Mock()
    mock_request.app.state.sortarr.oauth_manager = mock_oauth

    result = get_oauth_manager(mock_request.app.state.sortarr)
    assert result is mock_oauth


def test_get_oauth_manager_not_initialized(mock_request):
    """Test get_oauth_manager raises 500 when not initialized."""
    mock_request.app.state.sortarr.oauth_manager = None

    with pytest.raises(HTTPException) as exc_info:
        get_oauth_manager(mock_request.app.state.sortarr)

    assert exc_info.value.status_code == 500
    assert "OAuth manager not initialized" in exc_info.value.detail


def test_require_youtube_success(mock_request):
    """Test require_youtube returns YouTube client when authenticated."""
    mock_youtube = Mock()
    mock_request.app.state.sortarr.youtube_client = mock_youtube

    result = require_youtube(mock_request.app.state.sortarr)
    assert result is mock_youtube


def test_require_youtube_not_authenticated(mock_request):
    """Test require_youtube raises 401 when not authenticated."""
    mock_request.app.state.sortarr.youtube_client = None

    with pytest.raises(HTTPException) as exc_info:
        require_youtube(mock_request.app.state.sortarr)

    assert exc_info.value.status_code == 401
    assert "Not authenticated" in exc_info.value.detail


def test_get_runner_success(mock_request):
    """Test get_runner returns Runner when initialized."""
    mock_runner = Mock()
    mock_request.app.state.sortarr.runner = mock_runner

    result = get_runner(mock_request.app.state.sortarr)
    assert result is mock_runner


def test_get_runner_not_initialized(mock_request):
    """Test get_runner raises 503 when not initialized."""
    mock_request.app.state.sortarr.runner = None

    with pytest.raises(HTTPException) as exc_info:
        get_runner(mock_request.app.state.sortarr)

    assert exc_info.value.status_code == 503
    assert "Runner not initialized" in exc_info.value.detail
