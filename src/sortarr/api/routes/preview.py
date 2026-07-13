"""sortarr.api.routes.preview — dry-run preview routes."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends

from sortarr.api.deps import get_state
from sortarr.models.pipeline import (
    CachePreviewResponse,
    MockPreviewResponse,
    PreviewRequest,
)

if TYPE_CHECKING:
    from sortarr.api.app import AppState

log = logging.getLogger("sortarr.api.routes.preview")

router = APIRouter(tags=["preview"])


@router.post("/preview/mock", response_model=list[MockPreviewResponse])
def mock_preview(
    request: PreviewRequest,
    state: AppState = Depends(get_state),
) -> list[MockPreviewResponse]:
    """Run a mock preview with synthetic test activities.

    This endpoint exercises filter rules against synthetic activities
    without making any YouTube API calls (zero quota cost).

    Args:
        request: Optional pipeline_id to preview (None = all enabled)
        state: Application state from dependency injection

    Returns:
        List of mock preview results per pipeline
    """
    # TODO: Implement mock preview logic in T6.4
    # For now, return empty list (endpoint exists but not implemented)
    log.warning("mock preview not yet implemented (T6.4)")
    return []


@router.post("/preview/cache", response_model=list[CachePreviewResponse])
def cache_preview(
    request: PreviewRequest,
    state: AppState = Depends(get_state),
) -> list[CachePreviewResponse]:
    """Run a cache preview using activity_cache data.

    This endpoint runs filters against cached activities without
    making any YouTube API calls (zero quota cost).

    Args:
        request: Optional pipeline_id to preview (None = all enabled)
        state: Application state from dependency injection

    Returns:
        List of cache preview results per pipeline
    """
    # TODO: Implement cache preview logic in T6.4
    # For now, return empty list (endpoint exists but not implemented)
    log.warning("cache preview not yet implemented (T6.4)")
    return []
