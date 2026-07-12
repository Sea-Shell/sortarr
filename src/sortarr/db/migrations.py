"""
sortarr.db.migrations — Database schema and initialization.

Contains the canonical schema for sortarr v2 as a single SQL string,
plus helpers to apply it.  This is NOT a migration chain — it is the
one "current schema" applied idempotently on startup (CREATE IF NOT
EXISTS for every object).
"""

import sqlite3
import logging

log = logging.getLogger("sortarr.db.migrations")

V3_SCHEMA_SQL = """\
-- sortarr v2 schema — applied idempotently via CREATE IF NOT EXISTS.

-- Subscriptions
CREATE TABLE IF NOT EXISTS subscriptions (
    id TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    last_seen_at TEXT,
    created_at TEXT NOT NULL
);

-- Pipelines
CREATE TABLE IF NOT EXISTS pipelines (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    enabled INTEGER NOT NULL DEFAULT 1,
    destination_playlist_id TEXT NOT NULL,
    destination_playlist_title TEXT NOT NULL,
    selector_mode TEXT NOT NULL DEFAULT 'AND',
    subscription_scope TEXT NOT NULL DEFAULT 'all',
    duration_min_seconds INTEGER NOT NULL DEFAULT 0,
    duration_max_seconds INTEGER NOT NULL DEFAULT 0,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- Ignore Lists
CREATE TABLE IF NOT EXISTS ignore_lists (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    list_type TEXT NOT NULL CHECK(list_type IN ('word', 'video', 'subscription')),
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ignore_list_entries (
    id TEXT PRIMARY KEY,
    ignore_list_id TEXT NOT NULL REFERENCES ignore_lists(id) ON DELETE CASCADE,
    value TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ile_list ON ignore_list_entries(ignore_list_id);

-- Pipeline <-> Ignore-List junction
CREATE TABLE IF NOT EXISTS pipeline_ignore_lists (
    pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    ignore_list_id TEXT NOT NULL REFERENCES ignore_lists(id) ON DELETE CASCADE,
    PRIMARY KEY (pipeline_id, ignore_list_id)
);

-- Pipeline Selectors
CREATE TABLE IF NOT EXISTS pipeline_selectors (
    id TEXT PRIMARY KEY,
    pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    field TEXT NOT NULL,
    operator TEXT NOT NULL,
    pattern TEXT NOT NULL,
    combine_operator TEXT NOT NULL DEFAULT 'AND',
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_ps_pipeline ON pipeline_selectors(pipeline_id);

-- Pipeline Subscription Scope (for scope=selected)
CREATE TABLE IF NOT EXISTS pipeline_subscriptions (
    pipeline_id TEXT NOT NULL REFERENCES pipelines(id) ON DELETE CASCADE,
    subscription_id TEXT NOT NULL,
    PRIMARY KEY (pipeline_id, subscription_id)
);

-- Watermark Tracking (per-subscription, global)
CREATE TABLE IF NOT EXISTS subscription_tracking (
    subscription_id TEXT PRIMARY KEY,
    last_fetched_at TEXT,
    updated_at TEXT NOT NULL
);

-- Activity Cache — PERSISTENT (never cleared between runs)
CREATE TABLE IF NOT EXISTS activity_cache (
    video_id TEXT NOT NULL,
    subscription_id TEXT NOT NULL,
    title TEXT NOT NULL,
    channel_id TEXT NOT NULL,
    channel_title TEXT NOT NULL,
    video_type TEXT,
    description TEXT,
    published_at TEXT,
    duration_seconds INTEGER,
    collected_at TEXT NOT NULL,
    PRIMARY KEY (video_id, subscription_id)
);
CREATE INDEX IF NOT EXISTS idx_ac_published ON activity_cache(published_at);
CREATE INDEX IF NOT EXISTS idx_ac_subscription ON activity_cache(subscription_id);

-- Inserted Videos — audit trail
CREATE TABLE IF NOT EXISTS videos (
    video_id TEXT PRIMARY KEY,
    title TEXT,
    duration_seconds INTEGER,
    inserted_at TEXT NOT NULL,
    pipeline_id TEXT,
    pipeline_name TEXT,
    playlist_id TEXT,
    playlist_title TEXT
);

-- Pipeline Runs
CREATE TABLE IF NOT EXISTS pipeline_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    trigger TEXT NOT NULL DEFAULT 'scheduled',
    mode TEXT NOT NULL DEFAULT 'run',
    subscriptions_processed INTEGER DEFAULT 0,
    subscriptions_skipped INTEGER DEFAULT 0,
    videos_collected INTEGER DEFAULT 0,
    videos_after_cheap_filters INTEGER DEFAULT 0,
    videos_after_duration_filters INTEGER DEFAULT 0,
    videos_inserted INTEGER DEFAULT 0,
    quota_used INTEGER DEFAULT 0,
    errors INTEGER DEFAULT 0,
    error_message TEXT
);

-- Run Decisions (per-video audit from each run)
CREATE TABLE IF NOT EXISTS run_decisions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id INTEGER NOT NULL REFERENCES pipeline_runs(id),
    video_id TEXT NOT NULL,
    title TEXT,
    subscription_id TEXT,
    subscription_title TEXT,
    channel_id TEXT,
    pipeline_id TEXT,
    pipeline_name TEXT,
    action TEXT NOT NULL,
    filter_stage TEXT,
    filter_name TEXT,
    reason TEXT,
    duration_seconds INTEGER,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rd_run ON run_decisions(run_id);
CREATE INDEX IF NOT EXISTS idx_rd_video ON run_decisions(video_id);

-- App Config (key-value store)
CREATE TABLE IF NOT EXISTS app_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

-- OAuth Credentials (DB-backed, single row)
CREATE TABLE IF NOT EXISTS oauth_credentials (
    id INTEGER PRIMARY KEY CHECK(id = 1),
    access_token TEXT,
    refresh_token TEXT,
    token_uri TEXT,
    client_id TEXT,
    client_secret TEXT,
    scopes TEXT,
    expiry TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""

# Expected table count — sanity-check against schema drift.
EXPECTED_TABLE_COUNT = 14

# Expected index names — for verification.
EXPECTED_INDEXES = [
    "idx_ile_list",
    "idx_ps_pipeline",
    "idx_ac_published",
    "idx_ac_subscription",
    "idx_rd_run",
    "idx_rd_video",
]


def init_db(conn: sqlite3.Connection) -> None:
    """Apply the v2 schema to *conn*.

    Idempotent — safe to call multiple times (CREATE IF NOT EXISTS).
    Enables ``PRAGMA foreign_keys`` so that ON DELETE CASCADE actually
    fires (SQLite disables FK enforcement by default).
    """
    log.info("applying v2 database schema")
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(V3_SCHEMA_SQL)
    conn.commit()
    log.info("v2 database schema applied successfully")
