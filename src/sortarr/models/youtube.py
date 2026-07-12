"""sortarr.models.youtube — YouTube API data models."""

from __future__ import annotations

from pydantic import BaseModel


class Activity(BaseModel):
    """A YouTube activity item fetched via activities.list."""

    video_id: str
    title: str
    description: str = ""
    published_at: str  # ISO 8601
    channel_id: str
    channel_title: str
    subscription_id: str | None = None
    activity_type: str | None = None  # "upload", "playlistItem", etc.
    duration_seconds: int | None = None
    thumbnail_url: str | None = None


class Subscription(BaseModel):
    """A YouTube channel subscription."""

    subscription_id: str
    channel_id: str
    channel_title: str
    thumbnail_url: str | None = None


class Video(BaseModel):
    """An inserted video record."""

    video_id: str
    title: str
    channel_id: str
    channel_title: str
    published_at: str
    duration_seconds: int | None = None
    thumbnail_url: str | None = None
    pipeline_id: str
    playlist_id: str | None = None
    inserted_at: str | None = None


class HealthResponse(BaseModel):
    """API response for /api/health."""

    status: str = "ok"
    authenticated: bool = False
    next_scheduled_run: str | None = None
    pipelines_count: int = 0
    subscriptions_count: int = 0
    quota_used_today: int = 0
    quota_remaining: int = 10000


class ConfigResponse(BaseModel):
    """API response for GET /api/config."""

    schedule: str
    reprocess_days: int
    activity_limit: int
    subscription_limit: int
    published_after: str | None
    public_url: str
    log_level: str


class ConfigUpdate(BaseModel):
    """Request body for PUT /api/config — all fields optional for partial updates."""

    schedule: str | None = None
    reprocess_days: int | None = None
    activity_limit: int | None = None
    subscription_limit: int | None = None
    published_after: str | None = None
    public_url: str | None = None
    log_level: str | None = None
