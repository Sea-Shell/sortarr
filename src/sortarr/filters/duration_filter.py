"""sortarr.filters.duration_filter — Duration-based filter.

Checks video duration against pipeline min/max boundaries.
Runs AFTER batch enrichment — uses the shared duration_map.
Duration-unknown activities (None/0) are noted, not blocked.
"""

import logging

from sortarr.models.pipeline import FilterResult, FilterStage, PipelineConfig

log = logging.getLogger("sortarr.filters.duration")


def check_duration(
    activity: dict,
    pipeline: PipelineConfig,
    context: dict,
) -> FilterResult | None:
    """Check if activity duration falls within pipeline boundaries.

    Uses ``context['duration_map']`` — a ``dict[str, int]`` mapping
    video_id to duration_seconds.

    Duration of ``None`` or ``0`` is treated as unknown — logged, not blocked.

    Returns ``FilterResult(passed=False)`` when duration is outside boundaries,
    ``None`` when no duration limits are configured or duration is unknown.
    """
    min_sec = pipeline.duration_min_seconds
    max_sec = pipeline.duration_max_seconds

    # No duration limits configured — pass through
    if min_sec is None and max_sec is None:
        return None

    video_id = activity.get("video_id") or activity.get("id", "")
    duration_map: dict[str, int] = context.get("duration_map", {})
    duration = duration_map.get(video_id)

    # Unknown duration — log warning, don't block
    if duration is None or duration == 0:
        log.warning(
            "duration unknown for video %s — passing through (not blocked)",
            video_id,
        )
        return None

    if min_sec is not None and duration < min_sec:
        return FilterResult(
            filter_stage=FilterStage.DURATION,
            filter_name="duration_filter",
            passed=False,
            reason=f"duration {duration}s < minimum {min_sec}s",
        )

    if max_sec is not None and duration > max_sec:
        return FilterResult(
            filter_stage=FilterStage.DURATION,
            filter_name="duration_filter",
            passed=False,
            reason=f"duration {duration}s > maximum {max_sec}s",
        )

    return None  # passes all duration checks
