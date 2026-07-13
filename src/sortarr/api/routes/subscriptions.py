"""sortarr.api.routes.subscriptions — YouTube subscription routes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from sortarr.api.deps import get_state, require_youtube
from sortarr.db.repository import subscriptions

if TYPE_CHECKING:
    from sortarr.api.app import AppState
    from sortarr.core.youtube import YouTubeAPIClient

log = logging.getLogger("sortarr.api.routes.subscriptions")

router = APIRouter(tags=["subscriptions"])


class SubscriptionResponse(BaseModel):
    """API response for a subscription."""

    subscription_id: str = Field(description="YouTube subscription ID")
    channel_id: str = Field(description="YouTube channel ID")
    channel_title: str = Field(description="Channel title")


class SubscriptionStatsResponse(BaseModel):
    """API response for per-subscription statistics."""

    subscription_id: str = Field(description="YouTube subscription ID")
    channel_title: str = Field(description="Channel title")
    activities_count: int = Field(description="Number of activities in cache")
    last_fetched_at: str | None = Field(description="Last fetch timestamp (ISO 8601)")


@router.get("/subscriptions", response_model=list[SubscriptionResponse])
def list_subscriptions(
    state: AppState = Depends(get_state),
) -> list[SubscriptionResponse]:
    """List all subscriptions.

    Returns subscriptions from the database (populated by previous runs).

    Args:
        state: Application state from dependency injection

    Returns:
        List of subscriptions ordered by channel title
    """
    subs = subscriptions.list_subscriptions()
    return [
        SubscriptionResponse(
            subscription_id=sub.subscription_id,
            channel_id=sub.channel_id,
            channel_title=sub.channel_title,
        )
        for sub in subs
    ]


@router.get("/subscriptions/stats", response_model=list[SubscriptionStatsResponse])
def get_subscription_stats(
    state: AppState = Depends(get_state),
) -> list[SubscriptionStatsResponse]:
    """Get per-subscription statistics.

    Returns activity counts and last fetch timestamps for each subscription.

    Args:
        state: Application state from dependency injection

    Returns:
        List of subscription statistics
    """
    from sortarr.db.connection import get_connection

    conn = get_connection()
    rows = conn.execute("""
        SELECT 
            s.id,
            s.title,
            COUNT(ac.video_id) as activities_count,
            st.last_fetched_at
        FROM subscriptions s
        LEFT JOIN activity_cache ac ON s.id = ac.subscription_id
        LEFT JOIN subscription_tracking st ON s.id = st.subscription_id
        GROUP BY s.id, s.title, st.last_fetched_at
        ORDER BY s.title
    """).fetchall()

    return [
        SubscriptionStatsResponse(
            subscription_id=row["id"],
            channel_title=row["title"],
            activities_count=row["activities_count"],
            last_fetched_at=row["last_fetched_at"],
        )
        for row in rows
    ]


@router.get("/playlists", response_model=list[dict[str, Any]])
def list_playlists(
    youtube: YouTubeAPIClient = Depends(require_youtube),
    state: AppState = Depends(get_state),
) -> list[dict[str, Any]]:
    """List user's YouTube playlists.

    Requires authentication. Makes a live YouTube API call (1 quota unit).

    Args:
        youtube: YouTube API client from dependency injection
        state: Application state from dependency injection

    Returns:
        List of playlists with id, title, and thumbnail

    Raises:
        HTTPException: 401 if not authenticated
    """
    http = state.oauth_manager.get_http()
    response = youtube.get_playlists(http)

    playlists = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {})
        playlists.append(
            {
                "id": item.get("id", ""),
                "title": snippet.get("title", ""),
                "thumbnail": snippet.get("thumbnails", {})
                .get("default", {})
                .get("url", ""),
            }
        )

    log.info("fetched %d playlists", len(playlists))
    return playlists
