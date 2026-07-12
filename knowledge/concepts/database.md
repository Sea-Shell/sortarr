---
type: Datastore
title: Sortarr Database
description: SQLite persistence — connection handling, WAL mode, foreign keys, the v2 table schema, and the repository layer that wraps all queries.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr/db
tags: [sortarr, database, sqlite, persistence, wal, foreign-keys]
timestamp: 2026-07-12T14:00:00Z
---

# Layout

```
src/sortarr/db/
├── connection.py   # SQLite connection management (WAL mode, foreign keys)
├── migrations.py   # schema DDL (V3_SCHEMA_SQL), init_db()
└── repository/
    ├── config.py        # app_config key-value store
    ├── pipelines.py     # pipelines, selectors, ignore_lists, subscriptions, tracking
    ├── activities.py    # activity_cache (persistent)
    ├── videos.py        # inserted videos (audit trail)
    ├── runs.py          # pipeline_runs + run_decisions
    └── subscriptions.py # subscriptions table
```

# Migrations

`migrations.py` defines the schema as a single SQL string (`V3_SCHEMA_SQL`)
and exposes `init_db(conn)` which runs it via `executescript`. There is no
separate migrate command — startup is idempotent (`CREATE TABLE IF NOT EXISTS`).
`init_db` also enables `PRAGMA foreign_keys = ON` so that `ON DELETE CASCADE`
constraints fire (SQLite disables FK enforcement by default).

# Schema — V2 (14 tables)

| Table | Purpose |
|-------|---------|
| `subscriptions` | YouTube subscriptions — `id` PK, `title`, `channel_id` |
| `pipelines` | Pipeline configurations — `destination_playlist_id`, `selector_mode`, `subscription_scope`, `duration_min/max_seconds`, `sort_order` |
| `ignore_lists` | Named ignore lists — `list_type` CHECK `('word', 'video', 'subscription')` |
| `ignore_list_entries` | Entries in ignore lists — FK to `ignore_lists(id)` ON DELETE CASCADE |
| `pipeline_ignore_lists` | Junction: pipeline ↔ ignore list (composite PK) |
| `pipeline_selectors` | Selector rules per pipeline — `field`, `operator`, `pattern`, `combine_operator` |
| `pipeline_subscriptions` | Junction: pipeline ↔ subscription (for `scope=selected`) |
| `subscription_tracking` | Watermark per subscription — `last_fetched_at` |
| `activity_cache` | Persistent activity cache — PK `(video_id, subscription_id)`, never cleared between runs |
| `videos` | Audit trail of inserted videos — `pipeline_id`, `playlist_id` |
| `pipeline_runs` | Run history — `status`, `trigger`, `mode`, counts, `quota_used` |
| `run_decisions` | Per-video decisions from each run — FK to `pipeline_runs(id)` |
| `app_config` | Key-value store for runtime configuration |
| `oauth_credentials` | OAuth token storage — single row (`CHECK(id = 1)`) |

## Indexes

| Index | Table / Columns |
|-------|-----------------|
| `idx_ile_list` | `ignore_list_entries(ignore_list_id)` |
| `idx_ps_pipeline` | `pipeline_selectors(pipeline_id)` |
| `idx_ac_published` | `activity_cache(published_at)` |
| `idx_ac_subscription` | `activity_cache(subscription_id)` |
| `idx_rd_run` | `run_decisions(run_id)` |
| `idx_rd_video` | `run_decisions(video_id)` |

# Repository pattern

Handlers and the [pipeline](/knowledge/concepts/pipeline.md) never write SQL
inline — they call functions in `repository/` (e.g. `activities.upsert_activity`,
`pipelines.get_pipeline_selectors`, `runs.create_run`). The `Connection` is
created once and shared through [`AppState`](/knowledge/concepts/api.md).
