"""sortarr.api.deps — FastAPI dependency injection."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Depends, HTTPException, Request, status

if TYPE_CHECKING:
    from sortarr.api.app import AppState
    from sortarr.core.auth import OAuthManager
    from sortarr.core.runner import Runner
    from sortarr.core.youtube import YouTubeAPIClient


def get_state(request: Request) -> AppState:
    """Get application state from request.

    Available to all routes via dependency injection.
    """
    return request.app.state.sortarr


def get_oauth_manager(state: AppState = Depends(get_state)) -> OAuthManager:
    """Get OAuth manager from app state.

    Raises:
        HTTPException: 500 if OAuth manager not initialized
    """
    if state.oauth_manager is None:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth manager not initialized",
        )
    return state.oauth_manager


def require_youtube(state: AppState = Depends(get_state)) -> YouTubeAPIClient:
    """Require authenticated YouTube client.

    Raises:
        HTTPException: 401 if not authenticated
    """
    if state.youtube_client is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated — call /api/auth/login first",
        )
    return state.youtube_client


def get_runner(state: AppState = Depends(get_state)) -> Runner:
    """Get Runner from app state.

    Raises:
        HTTPException: 503 if Runner not initialized (not authenticated)
    """
    if state.runner is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Runner not initialized — authenticate first",
        )
    return state.runner
