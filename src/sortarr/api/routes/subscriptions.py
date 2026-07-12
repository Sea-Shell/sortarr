import logging
from datetime import datetime, timezone
from typing import List
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sortarr.api.deps import get_state
from sortarr.db.repository import videos as v

log = logging.getLogger("sortarr.api.subscriptions")
router = APIRouter()


class SubscriptionResponse(BaseModel):
    id: str
    title: str
    channel_id: str
    added_to_playlist_count: int = 0


class ActivityResponse(BaseModel):
    video_id: str
    title: str
    published_at: str
    video_type: str


def _get_added_count(con, sub_id: str) -> int:
    row = con.execute(
        "SELECT added_to_playlist_count FROM subscription WHERE id = ?", (sub_id,)
    ).fetchone()
    return (
        row["added_to_playlist_count"] if row and row["added_to_playlist_count"] else 0
    )


@router.get("/subscriptions", response_model=List[SubscriptionResponse])
async def list_subscriptions(request: Request):
    state = get_state(request)

    # Try to refresh subscriptions from YouTube API first
    if state.youtube:
        try:
            subs = state.youtube.get_subscriptions()
            now = datetime.now(timezone.utc).isoformat()
            for sub in subs:
                v.insert_subscription(state.db_con, sub.id, sub.title, now)
        except Exception as e:
            log.warning("Failed to sync subscriptions from YouTube, using cache: %s", e)

    # Serve from DB (always current if sync worked, cached if not)
    rows = state.db_con.execute(
        "SELECT id, title, COALESCE(added_to_playlist_count, 0) as added_to_playlist_count "
        "FROM subscription ORDER BY title ASC"
    ).fetchall()
    return [
        SubscriptionResponse(
            id=row["id"],
            title=row["title"],
            channel_id=row["id"],  # id == channel_id per YouTube client
            added_to_playlist_count=row["added_to_playlist_count"],
        )
        for row in rows
    ]


@router.get(
    "/subscriptions/{channel_id}/activity", response_model=List[ActivityResponse]
)
async def get_subscription_activity(channel_id: str, request: Request):
    state = get_state(request)

    # Try YouTube API first if available
    if state.youtube:
        try:
            activities = state.youtube.get_subscription_activity(channel_id)
            return [
                ActivityResponse(
                    video_id=a.video_id,
                    title=a.title,
                    published_at=a.published_at,
                    video_type=a.video_type,
                )
                for a in activities
            ]
        except Exception as e:
            log.warning(
                "YouTube activity fetch failed for %s, falling back to cache: %s",
                channel_id,
                e,
            )

    # Fall back to activity_cache
    cached = v.get_cached_activities(state.db_con, channel_id)
    if cached:
        return [
            ActivityResponse(
                video_id=row["video_id"],
                title=row["title"],
                published_at=row["published_at"],
                video_type=row["video_type"] or "",
            )
            for row in cached
        ]

    # No cache either
    raise HTTPException(
        status_code=503,
        detail=f"No cached activity for channel {channel_id} and YouTube API is unavailable",
    )
