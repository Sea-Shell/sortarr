"""sortarr.filters.word_filter — word-based title filter.

Checks if any word from word-type ignore list entries appears in the
activity title. Case-insensitive matching.
"""

import logging
from typing import Any

from sortarr.core.filters import register_filter
from sortarr.models.pipeline import FilterResult, FilterStage, PipelineConfig

log = logging.getLogger("sortarr.filters.word")


def check_word_filter(
    activity: dict[str, Any],
    pipeline: PipelineConfig,
    context: dict[str, Any],
) -> FilterResult | None:
    """Skip if activity title contains any word from word-type ignore lists.

    Reads ``context['word_ignore_values']`` — a ``set[str]`` of lowercase
    words pre-resolved by the runner from linked word-type ignore lists.

    Returns ``FilterResult(passed=False)`` when a match is found,
    ``None`` when not applicable (no words configured, or title is empty).
    """
    words: set[str] = context.get("word_ignore_values", set())
    if not words:
        return None

    title = (activity.get("title") or "").lower()
    if not title:
        return None

    for word in words:
        if word.lower() in title:
            log.debug(
                "word_filter hit: title=%r contains word=%r",
                activity.get("title"),
                word,
            )
            return FilterResult(
                filter_stage=FilterStage.CHEAP,
                filter_name="word_filter",
                passed=False,
                reason=f"title contains ignored word '{word}'",
            )
    return None


register_filter("word_filter", check_word_filter, FilterStage.CHEAP)
