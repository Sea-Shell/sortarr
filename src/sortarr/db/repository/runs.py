"""
sortarr.db.repository.runs — Pipeline run history and decisions.
"""

import logging

from sortarr.db.connection import get_connection
from sortarr.models.pipeline import RunSummary, RunSummaryResponse, RunDecisionResponse

log = logging.getLogger("sortarr.db.repository.runs")


def create_run(run_summary: RunSummary) -> int:
    """Create a new run record. Returns the run ID."""
    conn = get_connection()
    cursor = conn.execute("""
        INSERT INTO pipeline_runs (
            status, trigger, started_at, finished_at,
            subscriptions_processed, subscriptions_skipped,
            videos_collected, videos_after_cheap_filters,
            videos_after_duration_filters, videos_inserted,
            quota_used, error_message
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_summary.status, run_summary.trigger, run_summary.started_at,
        run_summary.completed_at,  # Model has completed_at, schema has finished_at
        run_summary.subscriptions_fetched, 0,  # subscriptions_skipped not in model
        run_summary.activities_collected, 0, 0,  # cheap/duration not in model
        run_summary.videos_inserted, run_summary.quota_used,
        run_summary.error_message
    ))
    conn.commit()
    return cursor.lastrowid or 0


def update_run(run_id: int, updates: dict) -> None:
    """Update a run record (partial update)."""
    conn = get_connection()
    fields = []
    values = []
    
    for key, value in updates.items():
        fields.append(f"{key} = ?")
        values.append(value)
    
    if fields:
        values.append(run_id)
        query = f"UPDATE pipeline_runs SET {', '.join(fields)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()


def get_run(run_id: int) -> RunSummaryResponse | None:
    """Get a run by ID."""
    conn = get_connection()
    row = conn.execute("""
        SELECT id, status, trigger, started_at, finished_at,
               subscriptions_processed, videos_collected,
               videos_after_cheap_filters, videos_after_duration_filters,
               videos_inserted, quota_used, error_message
        FROM pipeline_runs
        WHERE id = ?
    """, (run_id,)).fetchone()
    
    if not row:
        return None
    
    return RunSummaryResponse(
        id=str(row["id"]),
        status=row["status"],
        trigger=row["trigger"],
        started_at=row["started_at"],
        completed_at=row["finished_at"],  # Schema uses finished_at
        subscriptions_fetched=row["subscriptions_processed"],
        activities_collected=row["videos_collected"],
        videos_enriched=row["videos_after_cheap_filters"],
        videos_inserted=row["videos_inserted"],
        videos_skipped=0,  # Not tracked in schema
        quota_used=row["quota_used"],
        error_message=row["error_message"]
    )


def list_runs(limit: int = 50) -> list[RunSummaryResponse]:
    """List recent runs."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, status, trigger, started_at, finished_at,
               subscriptions_processed, videos_collected,
               videos_after_cheap_filters, videos_after_duration_filters,
               videos_inserted, quota_used, error_message
        FROM pipeline_runs
        ORDER BY started_at DESC
        LIMIT ?
    """, (limit,)).fetchall()
    
    return [
        RunSummaryResponse(
            id=str(row["id"]),
            status=row["status"],
            trigger=row["trigger"],
            started_at=row["started_at"],
            completed_at=row["finished_at"],
            subscriptions_fetched=row["subscriptions_processed"],
            activities_collected=row["videos_collected"],
            videos_enriched=row["videos_after_cheap_filters"],
            videos_inserted=row["videos_inserted"],
            videos_skipped=0,
            quota_used=row["quota_used"],
            error_message=row["error_message"]
        )
        for row in rows
    ]


def add_decisions(run_id: int, decisions: list[dict]) -> None:
    """Add run decisions (batch insert)."""
    if not decisions:
        return
    
    conn = get_connection()
    conn.executemany("""
        INSERT INTO run_decisions (
            run_id, video_id, pipeline_id, action,
            filter_stage, filter_name, reason, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, datetime('now'))
    """, [
        (
            run_id, d["video_id"], d.get("pipeline_id"), d["action"],
            d.get("filter_stage"), d.get("filter_name"), d.get("reason")
        )
        for d in decisions
    ])
    conn.commit()


def get_decisions(run_id: int, limit: int = 500) -> list[RunDecisionResponse]:
    """Get decisions for a run."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT run_id, pipeline_id, video_id, action,
               filter_stage, filter_name, reason
        FROM run_decisions
        WHERE run_id = ?
        ORDER BY id
        LIMIT ?
    """, (run_id, limit)).fetchall()
    
    return [
        RunDecisionResponse(
            run_id=str(row["run_id"]),
            pipeline_id=row["pipeline_id"] or "",
            video_id=row["video_id"],
            action=row["action"],
            filter_stage=row["filter_stage"],
            filter_name=row["filter_name"],
            reason=row["reason"]
        )
        for row in rows
    ]

