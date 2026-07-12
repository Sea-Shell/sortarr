"""sortarr.core.enricher — Batch duration enrichment.

Fetches video durations from YouTube's ``videos.list`` API in batches
of 50, then returns a ``duration_map`` mapping video_id → seconds.
"""

import logging
import re
from collections.abc import Callable
from typing import Any

log = logging.getLogger("sortarr.core.enricher")

# ISO 8601 duration regex — covers PnD, Th, Tm, Ts with optional fractional seconds
DURATION_RE = re.compile(
    r"^P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?$"
)


def parse_iso8601_duration(duration_str: str) -> int | None:
    """Parse ISO 8601 duration string to total seconds.

    Examples::

        "PT1H30M15S" → 5415
        "PT5M"       → 300
        "PT45S"      → 45
        "P1DT2H"     → 93600

    Returns ``None`` for unrecognised formats.
    """
    match = DURATION_RE.match(duration_str)
    if not match:
        return None

    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds_raw = match.group(4)
    seconds = round(float(seconds_raw)) if seconds_raw else 0

    return days * 86400 + hours * 3600 + minutes * 60 + seconds


class Enricher:
    """Batch video duration enrichment.

    Takes a callable that implements the ``videos.list`` response shape::

        get_videos_batch(video_ids_csv: str) -> dict  # {"items": [...]}

    The callable is injected — T3.1 builds the real ``YouTubeAPIClient``.
    """

    _BATCH_SIZE = 50

    def __init__(self, youtube_api: Callable[[str], Any]) -> None:
        self.youtube_api = youtube_api

    def batch_fetch(self, video_ids: set[str]) -> tuple[dict[str, int], list[str]]:
        """Fetch durations for *video_ids* in batches of 50.

        Returns: (duration_map, failed_video_ids)
        """
        ids_list = list(video_ids)
        duration_map: dict[str, int] = {}
        failed_ids: list[str] = []
        batch_count = 0

        for i in range(0, len(ids_list), self._BATCH_SIZE):
            batch = ids_list[i : i + self._BATCH_SIZE]
            ids_csv = ",".join(batch)
            batch_count += 1

            try:
                response = self.youtube_api(ids_csv)
                for item in response.get("items", []):
                    vid = item.get("id", "")
                    content_details = item.get("contentDetails", {}) or {}
                    duration_str = content_details.get("duration", "")
                    if duration_str:
                        seconds = parse_iso8601_duration(duration_str)
                        if seconds is not None:
                            duration_map[vid] = seconds
            except Exception:
                log.exception(
                    "batch enrichment failed for batch of %d videos", len(batch)
                )
                failed_ids.extend(batch)
                continue

        log.info(
            "enriched %d/%d video durations (%d batches, %d failed videos)",
            len(duration_map),
            len(video_ids),
            batch_count,
            len(failed_ids),
        )
        return duration_map, failed_ids
