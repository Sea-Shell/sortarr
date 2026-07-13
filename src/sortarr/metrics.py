"""sortarr.metrics — Prometheus metrics."""

from __future__ import annotations

from prometheus_client import Counter, Gauge, Histogram, generate_latest
from prometheus_client.core import CollectorRegistry

# Create a custom registry to avoid conflicts with other apps
registry = CollectorRegistry()

# Metrics
sortarr_runs_total = Counter(
    "sortarr_runs_total",
    "Total number of pipeline runs",
    ["trigger"],  # manual or scheduled
    registry=registry,
)

sortarr_quota_used_today = Gauge(
    "sortarr_quota_used_today",
    "YouTube API quota units used today",
    registry=registry,
)

sortarr_videos_inserted_total = Counter(
    "sortarr_videos_inserted_total",
    "Total number of videos inserted into playlists",
    registry=registry,
)

sortarr_run_duration_seconds = Histogram(
    "sortarr_run_duration_seconds",
    "Duration of pipeline runs in seconds",
    registry=registry,
)


def get_metrics_text() -> bytes:
    """Return Prometheus metrics in text format."""
    return generate_latest(registry)
