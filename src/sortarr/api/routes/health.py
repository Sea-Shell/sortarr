"""sortarr.api.routes.health — health check routes."""

import logging

from fastapi import APIRouter, Depends

from sortarr.api.deps import get_state
from sortarr.api.models import HealthResponse
from sortarr.core.youtube import get_quota_used

log = logging.getLogger("sortarr.api.routes.health")

router = APIRouter(prefix="/health", tags=["health"])

# YouTube API daily quota limit
DAILY_QUOTA_LIMIT = 10_000


@router.get("", response_model=HealthResponse)
async def health(state=Depends(get_state)) -> HealthResponse:
    """Health check endpoint.

    Returns:
        System status, auth state, next run time, counts, and quota.
    """
    from sortarr.db.connection import get_connection

    conn = get_connection()

    # Count pipelines
    pipelines_count = conn.execute("SELECT COUNT(*) FROM pipelines").fetchone()[0]

    # Count subscriptions
    subscriptions_count = conn.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[
        0
    ]

    # Get quota usage
    quota_used_today = get_quota_used()
    quota_remaining = max(0, DAILY_QUOTA_LIMIT - quota_used_today)

    # Get next scheduled run
    next_scheduled_run = None
    if state.scheduler:
        next_run = state.scheduler.get_next_run_time()
        if next_run:
            next_scheduled_run = next_run.isoformat()

    # Determine status
    authenticated = state.youtube_client is not None
    status = "ok" if authenticated else "degraded"

    return HealthResponse(
        status=status,
        authenticated=authenticated,
        next_scheduled_run=next_scheduled_run,
        pipelines_count=pipelines_count,
        subscriptions_count=subscriptions_count,
        quota_used_today=quota_used_today,
        quota_remaining=quota_remaining,
    )
