"""sortarr.filters.selector_filter — field/operator/pattern matching filter.

Evaluates pipeline selectors against activity fields. Supports operators:
contains, not_contains, equals, not_equals, starts_with, ends_with, regex.
"""

import logging
import re
from typing import Any

from sortarr.core.filters import register_filter
from sortarr.models.pipeline import FilterResult, FilterStage, PipelineConfig

log = logging.getLogger("sortarr.filters.selector")

# Fields from activity dict that selectors can target.
_ACTIVITY_FIELDS = {"title", "description", "channel_id", "channel_title", "video_id"}


def _apply_operator(field_value: str, operator: str, pattern: str) -> bool:
    """Apply a single operator to a field value. Returns True if matched."""
    fv = field_value.lower()
    pv = pattern.lower()

    if operator == "contains":
        return pv in fv
    elif operator == "not_contains":
        return pv not in fv
    elif operator == "equals":
        return fv == pv
    elif operator == "not_equals":
        return fv != pv
    elif operator == "starts_with":
        return fv.startswith(pv)
    elif operator == "ends_with":
        return fv.endswith(pv)
    elif operator == "regex":
        # Guard against catastrophic backtracking by limiting pattern complexity
        # Reject patterns with nested quantifiers like (a+)+ which can cause ReDoS
        if re.search(r'(\(.*[+*]\)|\[.*\])[+*{]', pattern):
            log.warning(
                "regex pattern %r rejected: nested quantifiers detected (potential ReDoS) — treating as no-match",
                pattern,
            )
            return False
        try:
            return bool(re.search(pattern, field_value, re.IGNORECASE))
        except re.error as e:
            log.warning("regex pattern %r is invalid: %s — treating as no-match", pattern, e)
            return False
    else:
        log.warning("unknown selector operator %r — treating as no-match", operator)
        return False


def check_selectors(
    activity: dict[str, Any],
    pipeline: PipelineConfig,
    context: dict[str, Any],
) -> FilterResult | None:
    """Evaluate pipeline selectors against activity fields.

    Reads ``context['selectors']`` — a ``list[dict]`` with keys
    ``field``, ``operator``, ``pattern``, ``combine_operator``.

    ``selector_mode`` comes from ``pipeline.selector_mode`` ("AND" or "OR").
    In AND mode every selector must match; in OR mode any one match suffices.

    Returns ``FilterResult(passed=False)`` when the selector set rejects the
    activity, ``None`` when no selectors are configured (no-op).
    """
    selectors: list[dict[str, Any]] = context.get("selectors", [])
    if not selectors:
        return None

    mode = pipeline.selector_mode or "AND"
    all_match = True
    any_match = False

    for sel in selectors:
        field = sel.get("field", "")
        operator = sel.get("operator", "contains")
        pattern = sel.get("pattern", "")
        field_value = str(activity.get(field, ""))

        matched = _apply_operator(field_value, operator, pattern)

        if matched:
            any_match = True
        else:
            all_match = False

        # Short-circuit: if AND already failed, or OR already succeeded
        if mode == "AND" and not all_match:
            break
        if mode == "OR" and any_match:
            break

    passed = all_match if mode == "AND" else any_match

    if not passed:
        log.debug(
            "selector filter rejected activity %r (mode=%s)",
            activity.get("video_id"),
            mode,
        )
        return FilterResult(
            filter_stage=FilterStage.CHEAP,
            filter_name="selector_filter",
            passed=False,
            reason=f"selectors not matched ({mode} mode)",
        )
    return None


register_filter("selector_filter", check_selectors, FilterStage.CHEAP)
