"""sortarr.api.models — API request/response models."""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="Service status (ok, degraded)")
    authenticated: bool = Field(description="Whether YouTube API is authenticated")
    next_scheduled_run: str | None = Field(
        description="Next scheduled pipeline run (ISO 8601)"
    )
    pipelines_count: int = Field(description="Number of configured pipelines")
    subscriptions_count: int = Field(description="Number of subscriptions")
    quota_used_today: int = Field(description="YouTube API quota used today")
    quota_remaining: int = Field(description="YouTube API quota remaining today")


class ConfigResponse(BaseModel):
    """Configuration response."""

    schedule: str = Field(description="Cron expression for pipeline runs")
    reprocess_days: int = Field(description="Days back for title similarity comparison")
    activity_limit: int = Field(
        description="Max activities per subscription per fetch (0=unlimited)"
    )
    subscription_limit: int = Field(
        description="Max subscriptions to fetch (0=unlimited)"
    )
    published_after: str | None = Field(
        description="ISO 8601 date override for watermark"
    )


class ConfigUpdate(BaseModel):
    """Partial configuration update."""

    schedule: str | None = Field(
        default=None, description="Cron expression for pipeline runs"
    )
    reprocess_days: int | None = Field(
        default=None, description="Days back for title similarity comparison"
    )
    activity_limit: int | None = Field(
        default=None, description="Max activities per subscription per fetch"
    )
    subscription_limit: int | None = Field(
        default=None, description="Max subscriptions to fetch"
    )
    published_after: str | None = Field(
        default=None, description="ISO 8601 date override for watermark"
    )


class ReorderRequest(BaseModel):
    """Request body for reordering pipelines."""

    pipeline_ids: list[str]


class SetJunctionRequest(BaseModel):
    """Request body for setting junction table associations."""

    ids: list[str]
