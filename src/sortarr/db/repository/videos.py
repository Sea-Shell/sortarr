"""
sortarr.db.repository.videos — Inserted videos audit trail.
"""

import logging

from sortarr.db.connection import get_connection
from sortarr.models.youtube import Video

log = logging.getLogger("sortarr.db.repository.videos")


def insert_video(video: Video) -> None:
    """Insert a video into the audit trail."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO videos (
            video_id, title, duration_seconds, inserted_at,
            pipeline_id, pipeline_name, playlist_id, playlist_title
        ) VALUES (?, ?, ?, datetime('now'), ?, ?, ?, ?)
    """, (
        video.video_id, video.title, video.duration_seconds,
        video.pipeline_id, None,  # pipeline_name not in Video model
        video.playlist_id, None  # playlist_title not in Video model
    ))
    conn.commit()


def get_video(video_id: str) -> Video | None:
    """Get a video by its YouTube video_id (most recent insert)."""
    conn = get_connection()
    row = conn.execute("""
        SELECT video_id, title, duration_seconds, inserted_at,
               pipeline_id, playlist_id
        FROM videos
        WHERE video_id = ?
        ORDER BY inserted_at DESC
        LIMIT 1
    """, (video_id,)).fetchone()
    
    if not row:
        return None
    
    # Map to Video model (need channel fields from somewhere else)
    return Video(
        video_id=row["video_id"],
        title=row["title"] or "",
        channel_id="",  # Not stored in videos table
        channel_title="",  # Not stored in videos table
        published_at="",  # Not stored in videos table
        duration_seconds=row["duration_seconds"],
        thumbnail_url=None,
        pipeline_id=row["pipeline_id"] or "",
        playlist_id=row["playlist_id"],
        inserted_at=row["inserted_at"]
    )


def video_exists(video_id: str, pipeline_id: str) -> bool:
    """Check if a video has already been inserted for a pipeline."""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM videos WHERE video_id = ? AND pipeline_id = ? LIMIT 1",
        (video_id, pipeline_id)
    ).fetchone()
    return row is not None


def search_videos(video_id: str) -> list[dict]:
    """Search for all insertions of a video across pipelines.
    
    Returns list of dicts (not Video objects, since schema doesn't match model).
    """
    conn = get_connection()
    rows = conn.execute("""
        SELECT video_id, title, duration_seconds, inserted_at,
               pipeline_id, pipeline_name, playlist_id, playlist_title
        FROM videos
        WHERE video_id = ?
        ORDER BY inserted_at DESC
    """, (video_id,)).fetchall()
    
    return [
        {
            "video_id": row["video_id"],
            "title": row["title"],
            "duration_seconds": row["duration_seconds"],
            "inserted_at": row["inserted_at"],
            "pipeline_id": row["pipeline_id"],
            "pipeline_name": row["pipeline_name"],
            "playlist_id": row["playlist_id"],
            "playlist_title": row["playlist_title"]
        }
        for row in rows
    ]
