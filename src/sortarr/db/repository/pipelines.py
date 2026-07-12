"""
sortarr.db.repository.pipelines — Pipeline repository.

Manages pipelines table and junction tables:
- pipeline_ignore_lists
- pipeline_selectors
- pipeline_subscriptions
"""

import logging
import uuid

from sortarr.db.connection import get_connection
from sortarr.models.pipeline import (
    PipelineConfig,
    PipelineCreate,
    PipelineResponse,
    PipelineUpdate,
)

log = logging.getLogger("sortarr.db.repository.pipelines")


def create_pipeline(config: PipelineCreate) -> PipelineConfig:
    """Create a new pipeline with optional junction table entries."""
    # Validate playlist_id
    if not config.playlist_id or not config.playlist_id.strip():
        raise ValueError("playlist_id is required and cannot be empty")
    
    pipeline_id = str(uuid.uuid4())
    conn = get_connection()

    # Note: destination_playlist_title is set to empty string initially
    # It will be populated when the playlist is first fetched from YouTube
    conn.execute(
        """
        INSERT INTO pipelines (
            id, name, enabled, destination_playlist_id, destination_playlist_title,
            selector_mode, subscription_scope, duration_min_seconds, duration_max_seconds,
            sort_order, created_at, updated_at
        ) VALUES (?, ?, 1, ?, '', ?, ?, ?, ?, 0, datetime('now'), datetime('now'))
    """,
        (
            pipeline_id,
            config.name,
            config.playlist_id or "",
            config.selector_mode,
            config.subscription_scope,
            config.duration_min_seconds or 0,
            config.duration_max_seconds or 0,
        ),
    )

    # Insert junction table entries if provided
    if config.ignore_list_ids:
        set_ignore_lists(pipeline_id, config.ignore_list_ids)

    if config.selector_ids:
        set_selectors(pipeline_id, config.selector_ids)

    if config.subscription_ids:
        set_subscriptions(pipeline_id, config.subscription_ids)

    conn.commit()
    log.info("created pipeline %s: %s", pipeline_id, config.name)
    return get_pipeline(pipeline_id)


def get_pipeline(pipeline_id: str) -> PipelineConfig:
    """Get a pipeline by ID."""
    conn = get_connection()
    row = conn.execute(
        """
        SELECT id, name, enabled, destination_playlist_id, sort_order,
               subscription_scope, duration_min_seconds, duration_max_seconds,
               selector_mode
        FROM pipelines
        WHERE id = ?
    """,
        (pipeline_id,),
    ).fetchone()

    if not row:
        raise ValueError(f"pipeline not found: {pipeline_id}")

    return PipelineConfig(
        id=row["id"],
        name=row["name"],
        enabled=bool(row["enabled"]),
        playlist_id=row["destination_playlist_id"] or None,
        order=row["sort_order"],
        subscription_scope=row["subscription_scope"],
        duration_min_seconds=row["duration_min_seconds"] or None,
        duration_max_seconds=row["duration_max_seconds"] or None,
        selector_mode=row["selector_mode"],
    )


def list_pipelines() -> list[PipelineResponse]:
    """List all pipelines with their junction table data."""
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT id, name, enabled, destination_playlist_id, sort_order,
               subscription_scope, duration_min_seconds, duration_max_seconds,
               selector_mode
        FROM pipelines
        ORDER BY sort_order, name
    """
    ).fetchall()

    pipelines = []
    for row in rows:
        pipeline_id = row["id"]
        pipelines.append(
            PipelineResponse(
                id=pipeline_id,
                name=row["name"],
                enabled=bool(row["enabled"]),
                order=row["sort_order"],
                playlist_id=row["destination_playlist_id"] or None,
                subscription_scope=row["subscription_scope"],
                duration_min_seconds=row["duration_min_seconds"] or None,
                duration_max_seconds=row["duration_max_seconds"] or None,
                selector_mode=row["selector_mode"],
                ignore_list_ids=get_pipeline_ignore_lists(pipeline_id),
                selector_ids=get_pipeline_selectors(pipeline_id),
                subscription_ids=get_pipeline_subscriptions(pipeline_id),
            )
        )

    return pipelines


def update_pipeline(pipeline_id: str, updates: PipelineUpdate) -> PipelineConfig:
    """Update a pipeline (partial update)."""
    conn = get_connection()

    # Build dynamic UPDATE query for non-None fields
    fields = []
    values = []

    if updates.name is not None:
        fields.append("name = ?")
        values.append(updates.name)
    if updates.enabled is not None:
        fields.append("enabled = ?")
        values.append(int(updates.enabled))
    if updates.playlist_id is not None:
        fields.append("destination_playlist_id = ?")
        values.append(updates.playlist_id)
    if updates.order is not None:
        fields.append("sort_order = ?")
        values.append(updates.order)
    if updates.subscription_scope is not None:
        fields.append("subscription_scope = ?")
        values.append(updates.subscription_scope)
    if updates.duration_min_seconds is not None:
        fields.append("duration_min_seconds = ?")
        values.append(updates.duration_min_seconds)
    if updates.duration_max_seconds is not None:
        fields.append("duration_max_seconds = ?")
        values.append(updates.duration_max_seconds)
    if updates.selector_mode is not None:
        fields.append("selector_mode = ?")
        values.append(updates.selector_mode)

    if fields:
        fields.append("updated_at = datetime('now')")
        values.append(pipeline_id)
        query = f"UPDATE pipelines SET {', '.join(fields)} WHERE id = ?"
        conn.execute(query, values)
        conn.commit()
        log.info("updated pipeline %s", pipeline_id)

    return get_pipeline(pipeline_id)


def delete_pipeline(pipeline_id: str) -> None:
    """Delete a pipeline (cascade deletes junction table entries via FK)."""
    conn = get_connection()
    conn.execute("DELETE FROM pipelines WHERE id = ?", (pipeline_id,))
    conn.commit()
    log.info("deleted pipeline %s", pipeline_id)


def reorder_pipelines(pipeline_ids: list[str]) -> None:
    """Reorder pipelines by setting sort_order."""
    conn = get_connection()
    for i, pipeline_id in enumerate(pipeline_ids):
        conn.execute(
            "UPDATE pipelines SET sort_order = ?, updated_at = datetime('now') WHERE id = ?",
            (i, pipeline_id),
        )
    conn.commit()
    log.info("reordered %d pipelines", len(pipeline_ids))


# Junction table helpers


def set_ignore_lists(pipeline_id: str, ignore_list_ids: list[str]) -> None:
    """Replace pipeline's ignore list associations."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM pipeline_ignore_lists WHERE pipeline_id = ?", (pipeline_id,)
    )
    if ignore_list_ids:
        conn.executemany(
            "INSERT INTO pipeline_ignore_lists (pipeline_id, ignore_list_id) VALUES (?, ?)",
            [(pipeline_id, iid) for iid in ignore_list_ids],
        )


def get_pipeline_ignore_lists(pipeline_id: str) -> list[str]:
    """Get ignore list IDs for a pipeline."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT ignore_list_id FROM pipeline_ignore_lists WHERE pipeline_id = ?",
        (pipeline_id,),
    ).fetchall()
    return [row["ignore_list_id"] for row in rows]


def set_selectors(pipeline_id: str, selector_ids: list[str]) -> None:
    """Replace pipeline's selector associations.

    Note: Selector CRUD is not yet implemented in Phase 3-4.
    """
    conn = get_connection()
    
    # Raise error if trying to add selectors
    if selector_ids:
        raise NotImplementedError(
            "Selector CRUD is not implemented. "
            "Use ignore lists for filtering in Phase 3-4."
        )
    
    # Allow clearing selectors
    conn.execute("DELETE FROM pipeline_selectors WHERE pipeline_id = ?", (pipeline_id,))


def get_pipeline_selectors(pipeline_id: str) -> list[str]:
    """Get selector IDs for a pipeline."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT id FROM pipeline_selectors WHERE pipeline_id = ?",
        (pipeline_id,),
    ).fetchall()
    return [row["id"] for row in rows]


def set_subscriptions(pipeline_id: str, subscription_ids: list[str]) -> None:
    """Replace pipeline's subscription associations."""
    conn = get_connection()
    conn.execute(
        "DELETE FROM pipeline_subscriptions WHERE pipeline_id = ?", (pipeline_id,)
    )
    if subscription_ids:
        conn.executemany(
            "INSERT INTO pipeline_subscriptions (pipeline_id, subscription_id) VALUES (?, ?)",
            [(pipeline_id, sid) for sid in subscription_ids],
        )


def get_pipeline_subscriptions(pipeline_id: str) -> list[str]:
    """Get subscription IDs for a pipeline."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT subscription_id FROM pipeline_subscriptions WHERE pipeline_id = ?",
        (pipeline_id,),
    ).fetchall()
    return [row["subscription_id"] for row in rows]
