"""sortarr.api.routes.stats — statistics routes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from sortarr.api.deps import get_state
from sortarr.db.repository import subscriptions

if TYPE_CHECKING:
    from sortarr.api.app import AppState

log = logging.getLogger("sortarr.api.routes.stats")

router = APIRouter(tags=["stats"])


class DashboardStatsResponse(BaseModel):
    """API response for dashboard statistics."""

    pipelines_count: int = Field(description="Total number of pipelines")
    pipelines_enabled_count: int = Field(description="Number of enabled pipelines")
    subscriptions_count: int = Field(description="Total number of subscriptions")
    activities_cached: int = Field(description="Number of activities in cache")
    total_runs: int = Field(description="Total number of pipeline runs")
    successful_runs: int = Field(description="Number of successful runs")
    failed_runs: int = Field(description="Number of failed runs")


@router.get("/stats", response_model=DashboardStatsResponse)
def get_dashboard_stats(
    state: AppState = Depends(get_state),
) -> DashboardStatsResponse:
    """Get dashboard statistics.

    Aggregates counts across pipelines, subscriptions, activities, and runs.

    Args:
        state: Application state from dependency injection

    Returns:
        Dashboard statistics
    """
    from sortarr.db.connection import get_connection

    conn = get_connection()

    # Pipeline counts
    pipeline_stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN enabled = 1 THEN 1 ELSE 0 END) as enabled
        FROM pipelines
    """).fetchone()

    # Subscription count
    sub_stats = subscriptions.get_subscription_stats()

    # Activity cache count
    activity_count = conn.execute("""
        SELECT COUNT(*) as count FROM activity_cache
    """).fetchone()

    # Run counts
    run_stats = conn.execute("""
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as successful,
            SUM(CASE WHEN status = 'failed' THEN 1 ELSE 0 END) as failed
        FROM pipeline_runs
    """).fetchone()

    return DashboardStatsResponse(
        pipelines_count=pipeline_stats["total"],
        pipelines_enabled_count=pipeline_stats["enabled"] or 0,
        subscriptions_count=sub_stats["count"],
        activities_cached=activity_count["count"],
        total_runs=run_stats["total"],
        successful_runs=run_stats["successful"] or 0,
        failed_runs=run_stats["failed"] or 0,
    )
