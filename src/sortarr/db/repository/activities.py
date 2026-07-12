"""
sortarr.db.repository.activities — Activity cache repository.

Manages the persistent activity_cache table.
"""

import logging
from datetime import UTC, datetime, timedelta

from sortarr.db.connection import get_connection
from sortarr.models.youtube import Activity

log = logging.getLogger("sortarr.db.repository.activities")


def upsert_activities(activities: list[Activity]) -> None:
    """Batch upsert activities into the cache.

    Uses UNIQUE(video_id, subscription_id) constraint for idempotency.
    """
    if not activities:
        return

    conn = get_connection()
    conn.executemany(
        """
        INSERT INTO activity_cache (
            video_id, title, description, published_at,
            channel_id, channel_title, subscription_id,
            video_type, duration_seconds, collected_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))
        ON CONFLICT(video_id, subscription_id) DO UPDATE SET
            title = excluded.title,
            description = excluded.description,
            published_at = excluded.published_at,
            channel_id = excluded.channel_id,
            channel_title = excluded.channel_title,
            video_type = excluded.video_type,
            duration_seconds = COALESCE(excluded.duration_seconds, activity_cache.duration_seconds),
            collected_at = datetime('now')
    """,
        [
            (
                a.video_id,
                a.title,
                a.description,
                a.published_at,
                a.channel_id,
                a.channel_title,
                a.subscription_id,
                a.activity_type,
                a.duration_seconds,
            )
            for a in activities
        ],
    )
    conn.commit()
    log.info("upserted %d activities into cache", len(activities))


def get_activities(subscription_ids: list[str] | None = None) -> list[Activity]:
    """Load activities from cache, optionally filtered by subscription IDs."""
    conn = get_connection()

    if subscription_ids:
        placeholders = ",".join("?" * len(subscription_ids))
        query = f"""
            SELECT video_id, title, description, published_at,
                   channel_id, channel_title, subscription_id,
                   video_type, duration_seconds
            FROM activity_cache
            WHERE subscription_id IN ({placeholders})
            ORDER BY published_at DESC
        """
        rows = conn.execute(query, subscription_ids).fetchall()
    else:
        query = """
            SELECT video_id, title, description, published_at,
                   channel_id, channel_title, subscription_id,
                   video_type, duration_seconds
            FROM activity_cache
            ORDER BY published_at DESC
        """
        rows = conn.execute(query).fetchall()

    return [
        Activity(
            video_id=row["video_id"],
            title=row["title"],
            description=row["description"],
            published_at=row["published_at"],
            channel_id=row["channel_id"],
            channel_title=row["channel_title"],
            subscription_id=row["subscription_id"],
            activity_type=row["video_type"],
            duration_seconds=row["duration_seconds"],
        )
        for row in rows
    ]


def get_cached_duration(video_id: str) -> int | None:
    """Lookup cached duration for a video."""
    conn = get_connection()
    row = conn.execute(
        "SELECT duration_seconds FROM activity_cache WHERE video_id = ? LIMIT 1",
        (video_id,),
    ).fetchone()
    return row["duration_seconds"] if row else None


def update_duration(video_id: str, duration_seconds: int) -> None:
    """Update duration for a cached activity."""
    conn = get_connection()
    conn.execute(
        "UPDATE activity_cache SET duration_seconds = ? WHERE video_id = ?",
        (duration_seconds, video_id),
    )
    conn.commit()


def prune_old_entries(retention_days: int = 30) -> int:
    """Delete entries older than retention_days.

    Returns the number of rows deleted.
    """
    cutoff = (datetime.now(UTC) - timedelta(days=retention_days)).isoformat()
    conn = get_connection()
    cursor = conn.execute(
        "DELETE FROM activity_cache WHERE collected_at < ?",
        (cutoff,),
    )
    deleted = cursor.rowcount
    conn.commit()
    log.info("pruned %d activities older than %d days", deleted, retention_days)
    return deleted


def get_cache_stats() -> dict:
    """Get cache statistics."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT
            COUNT(*) as count,
            MIN(collected_at) as oldest,
            MAX(collected_at) as newest
        FROM activity_cache
    """
    ).fetchone()

    return {
        "count": row["count"],
        "oldest": row["oldest"],
        "newest": row["newest"],
    }

