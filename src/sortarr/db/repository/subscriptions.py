"""
sortarr.db.repository.subscriptions — YouTube subscriptions and tracking.
"""

import logging

from sortarr.db.connection import get_connection
from sortarr.models.youtube import Subscription

log = logging.getLogger("sortarr.db.repository.subscriptions")


def upsert_subscriptions(subs: list[Subscription]) -> None:
    """Batch upsert subscriptions."""
    if not subs:
        return
    
    conn = get_connection()
    conn.executemany("""
        INSERT INTO subscriptions (
            id, channel_id, title, created_at
        ) VALUES (?, ?, ?, datetime('now'))
        ON CONFLICT(id) DO UPDATE SET
            title = excluded.title,
            channel_id = excluded.channel_id
    """, [
        (s.subscription_id, s.channel_id, s.channel_title)
        for s in subs
    ])
    conn.commit()
    log.info("upserted %d subscriptions", len(subs))


def list_subscriptions() -> list[Subscription]:
    """List all subscriptions."""
    conn = get_connection()
    rows = conn.execute("""
        SELECT id, channel_id, title
        FROM subscriptions
        ORDER BY title
    """).fetchall()
    
    return [
        Subscription(
            subscription_id=row["id"],
            channel_id=row["channel_id"],
            channel_title=row["title"],
            thumbnail_url=None
        )
        for row in rows
    ]


def get_subscription_stats() -> dict:
    """Get subscription statistics."""
    conn = get_connection()
    row = conn.execute("SELECT COUNT(*) as count FROM subscriptions").fetchone()
    return {"count": row["count"]}


def update_tracking(subscription_id: str, last_fetched_at: str) -> None:
    """Update subscription tracking (watermark)."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO subscription_tracking (subscription_id, last_fetched_at, updated_at)
        VALUES (?, ?, datetime('now'))
        ON CONFLICT(subscription_id) DO UPDATE SET
            last_fetched_at = excluded.last_fetched_at,
            updated_at = datetime('now')
    """, (subscription_id, last_fetched_at))
    conn.commit()


def get_tracking(subscription_id: str) -> dict | None:
    """Get tracking data for a subscription."""
    conn = get_connection()
    row = conn.execute("""
        SELECT last_fetched_at
        FROM subscription_tracking
        WHERE subscription_id = ?
    """, (subscription_id,)).fetchone()
    
    if not row:
        return None
    
    return {
        "last_fetched_at": row["last_fetched_at"]
    }
