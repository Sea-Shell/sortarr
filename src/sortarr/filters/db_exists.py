"""sortarr.filters.db_exists — database deduplication filter.

Checks if a video_id already exists in the videos table for the given pipeline.
"""

import logging
from typing import Any

from sortarr.core.filters import register_filter
from sortarr.models.pipeline import FilterResult, FilterStage, PipelineConfig

log = logging.getLogger("sortarr.filters.db_exists")


def check_db_exists(
    activity: dict[str, Any],
    pipeline: PipelineConfig,
    context: dict[str, Any],
) -> FilterResult | None:
    """Skip if video_id already exists in the videos table for this pipeline.

    Reads ``context['existing_video_ids']`` — a ``set[str]`` of video IDs
    pre-loaded by the runner from the ``videos`` table.

    Returns ``FilterResult(passed=False)`` when a match is found,
    ``None`` when not applicable (no existing videos, or video_id missing).
    """
    existing: set[str] = context.get("existing_video_ids", set())
    if not existing:
        return None

    video_id = activity.get("video_id", "")
    if not video_id:
        return None

    if video_id in existing:
        log.debug("db_exists hit: video_id=%r already in videos table", video_id)
        return FilterResult(
            filter_stage=FilterStage.CHEAP,
            filter_name="db_exists",
            passed=False,
            reason=f"video {video_id} already exists in database",
        )
    return None


register_filter("db_exists", check_db_exists, FilterStage.CHEAP)
