"""sortarr.filters.title_similarity — title similarity filter.

Rejects near-duplicate titles already in the DB using Levenshtein distance.
"""

import logging
from typing import Any

from sortarr.core.filters import register_filter
from sortarr.models.pipeline import FilterResult, FilterStage, PipelineConfig

log = logging.getLogger("sortarr.filters.title_similarity")


def _normalize(text: str) -> str:
    """Lowercase and collapse non-alphanumeric runs to single spaces."""
    import re
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def _levenshtein(a: str, b: str) -> int:
    """Compute Levenshtein edit distance between two strings."""
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Optimise: only need two rows at a time
    prev = list(range(len(b) + 1))
    curr = [0] * (len(b) + 1)

    for i, ca in enumerate(a):
        curr[0] = i + 1
        for j, cb in enumerate(b):
            cost = 0 if ca == cb else 1
            curr[j + 1] = min(
                prev[j + 1] + 1,      # deletion
                curr[j] + 1,           # insertion
                prev[j] + cost,        # substitution
            )
        prev, curr = curr, prev

    return prev[len(b)]


def _fuzz_ratio(a: str, b: str, max_len: int = 500) -> int:
    """Similarity ratio (0–100) between two strings using Levenshtein.
    
    Strings longer than max_len are truncated to prevent O(n*m) explosion.
    """
    if not a or not b:
        return 0
    na, nb = _normalize(a), _normalize(b)
    if not na or not nb:
        return 0
    # Truncate to prevent blocking computation
    na = na[:max_len]
    nb = nb[:max_len]
    max_len_actual = max(len(na), len(nb))
    if max_len_actual == 0:
        return 0
    dist = _levenshtein(na, nb)
    return int((1 - dist / max_len_actual) * 100)


def check_title_similarity(
    activity: dict[str, Any],
    pipeline: PipelineConfig,
    context: dict[str, Any],
) -> FilterResult | None:
    """Skip if activity title is too similar to a recently inserted video.

    Reads ``context['recent_videos']`` — a ``list[dict]`` with ``title`` key
    from the ``videos`` table, scoped to ``reprocess_days``.

    Reads ``context['compare_distance']`` — int threshold (0–100, default 80).
    Titles with similarity ratio >= threshold are rejected.

    Returns ``FilterResult(passed=False)`` when a duplicate is found,
    ``None`` when not applicable (no recent videos, or threshold not met).
    """
    recent_videos: list[dict[str, Any]] = context.get("recent_videos", [])
    if not recent_videos:
        return None

    compare_distance: int = context.get("compare_distance", 80)
    title = activity.get("title", "")
    if not title:
        return None

    for entry in recent_videos:
        existing_title = entry.get("title", "")
        ratio = _fuzz_ratio(title, existing_title)
        if ratio >= compare_distance:
            video_id = entry.get("video_id", "unknown")
            log.debug(
                "title_similarity hit: title=%r similar to %r (ratio=%d%%)",
                title,
                existing_title,
                ratio,
            )
            return FilterResult(
                filter_stage=FilterStage.CHEAP,
                filter_name="title_similarity",
                passed=False,
                reason=f"title similar to {video_id} ({ratio}%)",
            )
    return None


register_filter("title_similarity", check_title_similarity, FilterStage.CHEAP)
