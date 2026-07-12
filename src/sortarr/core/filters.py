"""sortarr.core.filters — Filter chain engine.

Orchestrates the ordered execution of filters on activities.
Cheap filters run before any YouTube API calls (duration enrichment).
"""

from __future__ import annotations

import logging
from typing import Any

from sortarr.models.pipeline import FilterResult, FilterStage, PipelineConfig

log = logging.getLogger("sortarr.core.filters")

# Type alias for a filter function signature.
FilterFunc = Any  # (dict, PipelineConfig, dict) -> FilterResult | None

# Registry of filter functions in execution order.
# Each entry: (name, func, filter_stage)
FILTER_REGISTRY: list[tuple[str, FilterFunc, FilterStage]] = []


def register_filter(name: str, func: FilterFunc, stage: FilterStage) -> None:
    """Register a filter function. Called by each filter module at import time."""
    FILTER_REGISTRY.append((name, func, stage))
    log.debug("registered filter: %s (stage=%s)", name, stage.value)


class FilterChain:
    """Orchestrates filter execution in order.

    Cheap filters run first and short-circuit on first failure.
    Duration filters run after batch enrichment via ``run_duration_filter``.
    """

    def __init__(
        self, pipeline: PipelineConfig, context: dict[str, Any] | None = None
    ) -> None:
        self.pipeline = pipeline
        self.context = context or {}

    def run_cheap_filters(self, activity: dict[str, Any]) -> FilterResult | None:
        """Run all cheap filters in order.

        Returns the first ``FilterResult(passed=False)`` or ``None`` if all pass.
        Short-circuits on first failure — subsequent filters are not called.
        """
        for name, func, stage in FILTER_REGISTRY:
            if stage != FilterStage.CHEAP:
                continue
            result = func(activity, self.pipeline, self.context)
            if result is not None and not result.passed:
                log.debug(
                    "cheap filter %s rejected activity %s: %s",
                    name,
                    activity.get("video_id"),
                    result.reason,
                )
                return result
        return None

    def run_duration_filter(
        self, activity: dict[str, Any], duration_map: dict[str, int]
    ) -> FilterResult | None:
        """Run duration filter using the shared duration_map.

        Called AFTER batch enrichment — the duration_map maps video_id to seconds.
        """
        # Lazy import to avoid circular dependency at module level.
        from sortarr.filters.duration_filter import check_duration

        return check_duration(activity, self.pipeline, {"duration_map": duration_map})
