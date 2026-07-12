"""
sortarr.db.repository.config — App config key-value store.

Uses the app_config table for simple key-value persistence.
"""

import logging
from sortarr.db.connection import get_connection

log = logging.getLogger("sortarr.db.repository.config")


def get_config() -> dict[str, str]:
    """Get all config key-value pairs."""
    conn = get_connection()
    rows = conn.execute("SELECT key, value FROM app_config").fetchall()
    return {row["key"]: row["value"] for row in rows}


def set_config(key: str, value: str) -> None:
    """Set a config key-value pair."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO app_config (key, value) VALUES (?, ?)
        ON CONFLICT(key) DO UPDATE SET value = excluded.value
    """, (key, value))
    conn.commit()


def get_config_value(key: str, default: str | None = None) -> str | None:
    """Get a single config value."""
    conn = get_connection()
    row = conn.execute("SELECT value FROM app_config WHERE key = ?", (key,)).fetchone()
    return row["value"] if row else default
