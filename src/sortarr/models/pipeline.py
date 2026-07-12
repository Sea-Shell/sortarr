"""sortarr.models.pipeline — pipeline and configuration models."""

from __future__ import annotations

import uuid
from enum import Enum

from pydantic import BaseModel, Field


class FilterStage(str, Enum):
    """Classification of filter stages in the pipeline chain."""

    CHEAP = "cheap"
    DURATION = "duration"


class FilterResult(BaseModel):
    """Result of a single filter evaluating an activity."""

    filter_stage: FilterStage
    filter_name: str
    passed: bool
    reason: str | None = None


class PipelineConfig(BaseModel):
    """Full pipeline configuration as stored in DB / returned to API."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    enabled: bool = True
    playlist_id: str | None = None
    order: int = 0

    # Filter config
    subscription_scope: str = "all"  # "all" or "selected"
    duration_min_seconds: int | None = None
    duration_max_seconds: int | None = None
    selector_mode: str = "AND"  # "AND" or "OR"


class PipelineCreate(BaseModel):
    """Request body for creating a new pipeline."""

    name: str
    playlist_id: str | None = None
    subscription_scope: str = "all"
    duration_min_seconds: int | None = None
    duration_max_seconds: int | None = None
    selector_mode: str = "AND"
    ignore_list_ids: list[str] = Field(default_factory=list)
    selector_ids: list[str] = Field(default_factory=list)
    subscription_ids: list[str] = Field(default_factory=list)


class PipelineUpdate(BaseModel):
    """Request body for partial pipeline update — all fields optional."""

    name: str | None = None
    enabled: bool | None = None
    playlist_id: str | None = None
    order: int | None = None
    subscription_scope: str | None = None
    duration_min_seconds: int | None = None
    duration_max_seconds: int | None = None
    selector_mode: str | None = None


class PipelineResponse(BaseModel):
    """API response for a pipeline."""

    id: str
    name: str
    enabled: bool
    order: int
    playlist_id: str | None
    subscription_scope: str
    duration_min_seconds: int | None
    duration_max_seconds: int | None
    selector_mode: str
    ignore_list_ids: list[str] = Field(default_factory=list)
    selector_ids: list[str] = Field(default_factory=list)
    subscription_ids: list[str] = Field(default_factory=list)


class RunSummary(BaseModel):
    """Pipeline run summary as stored internally."""

    id: str | None = None
    status: str = "running"  # running, completed, failed, completed_quota_blocked
    trigger: str = "manual"  # manual, scheduled
    started_at: str | None = None
    completed_at: str | None = None
    subscriptions_fetched: int = 0
    activities_collected: int = 0
    videos_enriched: int = 0
    videos_inserted: int = 0
    videos_skipped: int = 0
    quota_used: int = 0
    error_message: str | None = None


class RunSummaryResponse(BaseModel):
    """API response for a pipeline run summary."""

    id: str
    status: str
    trigger: str
    started_at: str | None
    completed_at: str | None
    subscriptions_fetched: int
    activities_collected: int
    videos_enriched: int
    videos_inserted: int
    videos_skipped: int
    quota_used: int
    error_message: str | None


class RunDecisionResponse(BaseModel):
    """API response for a single run decision (per video)."""

    run_id: str
    pipeline_id: str
    video_id: str
    action: str  # "inserted" or "skipped"
    filter_stage: str | None  # "cheap", "duration", or null
    filter_name: str | None  # which filter skipped it
    reason: str | None


class PreviewRequest(BaseModel):
    """Request body for preview endpoints."""

    pipeline_id: str | None = None  # None = all enabled pipelines


class MockActivity(BaseModel):
    """A synthetic activity used in mock preview to exercise filter rules."""

    video_id: str
    title: str
    description: str = ""
    channel_id: str
    channel_title: str
    subscription_id: str
    published_at: str
    activity_type: str = "upload"
    duration_seconds: int | None = None
    label: str = ""  # descriptive label for what this mock tests


class MockPreviewResponse(BaseModel):
    """API response for mock preview of a single pipeline."""

    pipeline_id: str
    pipeline_name: str
    activities: list[MockActivity]
    results: list[dict] = []  # filter result per activity
    quota_cost: int = 0


class CachePreviewResponse(BaseModel):
    """API response for cache preview of a single pipeline."""

    pipeline_id: str
    pipeline_name: str
    total_activities: int
    activities_after_cheap: int
    activities_after_duration: int
    duration_unknown_count: int = 0
    quota_cost: int = 0
