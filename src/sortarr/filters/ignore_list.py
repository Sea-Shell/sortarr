"""sortarr.filters.ignore_list — ignore-list filter.

Two functions: one for subscription-level ignores and one for video-level
ignores. Both check membership against pre-resolved sets in context.
"""

import logging
from typing import Any

from sortarr.core.filters import register_filter
from sortarr.models.pipeline import FilterResult, FilterStage, PipelineConfig

log = logging.getLogger("sortarr.filters.ignore_list")


def check_subscription_ignore(
    activity: dict[str, Any],
    pipeline: PipelineConfig,
    context: dict[str, Any],
) -> FilterResult | None:
    """Skip if activity's subscription_id is in the subscription ignore list.

    Reads ``context['subscription_ignore_ids']`` — a ``set[str]`` of
    subscription IDs pre-resolved by the runner.

    Returns ``FilterResult(passed=False)`` when matched,
    ``None`` when not applicable (no ignores configured, or subscription_id missing).
    """
    ignore_ids: set[str] = context.get("subscription_ignore_ids", set())
    if not ignore_ids:
        return None

    sub_id = activity.get("subscription_id", "")
    if not sub_id:
        return None

    if sub_id in ignore_ids:
        log.debug("subscription_ignore hit: subscription_id=%r", sub_id)
        return FilterResult(
            filter_stage=FilterStage.CHEAP,
            filter_name="subscription_ignore",
            passed=False,
            reason=f"subscription {sub_id} is in ignore list",
        )
    return None


def check_video_ignore(
    activity: dict[str, Any],
    pipeline: PipelineConfig,
    context: dict[str, Any],
) -> FilterResult | None:
    """Skip if activity's video_id is in the video ignore list.

    Reads ``context['video_ignore_ids']`` — a ``set[str]`` of video IDs
    pre-resolved by the runner.

    Returns ``FilterResult(passed=False)`` when matched,
    ``None`` when not applicable (no ignores configured, or video_id missing).
    """
    ignore_ids: set[str] = context.get("video_ignore_ids", set())
    if not ignore_ids:
        return None

    video_id = activity.get("video_id", "")
    if not video_id:
        return None

    if video_id in ignore_ids:
        log.debug("video_ignore hit: video_id=%r", video_id)
        return FilterResult(
            filter_stage=FilterStage.CHEAP,
            filter_name="video_ignore",
            passed=False,
            reason=f"video {video_id} is in ignore list",
        )
    return None


register_filter("subscription_ignore", check_subscription_ignore, FilterStage.CHEAP)
register_filter("video_ignore", check_video_ignore, FilterStage.CHEAP)
