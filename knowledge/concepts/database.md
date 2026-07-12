---
type: Datastore
title: Sortarr Database
description: SQLite persistence — connection handling, WAL mode, foreign keys, the v2 table schema, and the repository layer that wraps all queries.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr/db
tags: [sortarr, database, sqlite, persistence, wal, foreign-keys]
timestamp: 2026-07-12T23:00:00Z
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
inline — they call functions in `repository/` (e.g. `activities.upsert_activities`,
`pipelines.get_pipeline_selectors`, `runs.create_run`). The `Connection` is
created once and shared through [`AppState`](/knowledge/concepts/api.md).

## Activity Cache Repository (`activities.py`)

The activity cache repository manages the persistent `activity_cache` table,
which stores fetched YouTube activities between runs for cache preview and
UI fallback.

### Operations

| Function | Purpose |
|----------|---------|
| `upsert_activities(activities)` | Batch insert/update activities. Uses `ON CONFLICT(video_id, subscription_id) DO UPDATE` for idempotency. Preserves existing `duration_seconds` via `COALESCE` if new value is `None`. |
| `get_activities(subscription_ids?)` | Load activities from cache, optionally filtered by subscription IDs. Returns list ordered by `published_at DESC`. |
| `get_cached_duration(video_id)` | Lookup cached duration for a video. Returns `int | None`. |
| `update_duration(video_id, duration_seconds)` | Update duration for a cached activity. Used by enricher after `videos.list` call. |
| `prune_old_entries(retention_days=30)` | Delete entries older than `retention_days` based on `collected_at`. Returns count of deleted rows. |
| `get_cache_stats()` | Get cache statistics: `count`, `oldest`, `newest` (based on `collected_at`). |

### Schema mapping

The repository maps between the `Activity` model and the `activity_cache` table:

- Model field `activity_type` ↔ DB column `video_type`
- Model field `subscription_id` ↔ DB column `subscription_id`
- DB column `collected_at` is auto-set to `datetime('now')` on insert/update

### Idempotency guarantee

`upsert_activities` uses the composite PK `(video_id, subscription_id)` for
conflict detection. Upserting the same activity twice updates the row rather
than creating a duplicate. This is critical for the runner's activity collection
phase, which may re-fetch the same videos across multiple runs.

## Pipelines Repository (`pipelines.py`)

The pipelines repository manages the `pipelines` table and its three junction
tables: `pipeline_ignore_lists`, `pipeline_selectors`, and `pipeline_subscriptions`.

### Core CRUD Operations

| Function | Purpose |
|----------|---------|
| `create_pipeline(config: PipelineCreate)` | Create a new pipeline with optional junction table entries (ignore lists, selectors, subscriptions). Returns `PipelineConfig`. Auto-generates UUID. Sets `destination_playlist_title` to empty string (populated on first YouTube fetch). |
| `get_pipeline(pipeline_id: str)` | Get a single pipeline by ID. Raises `ValueError` if not found. Returns `PipelineConfig`. |
| `list_pipelines()` | List all pipelines with their junction table data. Returns `list[PipelineResponse]`. Ordered by `sort_order`, then `name`. |
| `update_pipeline(pipeline_id, updates: PipelineUpdate)` | Partial update of pipeline fields. Only non-`None` fields in `updates` are applied. Returns updated `PipelineConfig`. |
| `delete_pipeline(pipeline_id: str)` | Delete a pipeline. Cascade deletes junction table entries via FK constraints. |
| `reorder_pipelines(pipeline_ids: list[str])` | Set `sort_order` for pipelines. First ID gets `sort_order=0`, second gets `1`, etc. |

### Junction Table Helpers

| Function | Purpose |
|----------|---------|
| `set_ignore_lists(pipeline_id, ignore_list_ids)` | Replace pipeline's ignore list associations. Deletes existing, inserts new. |
| `get_pipeline_ignore_lists(pipeline_id)` | Get ignore list IDs for a pipeline. Returns `list[str]`. |
| `set_selectors(pipeline_id, selector_ids)` | Replace pipeline's selector associations. Simplified implementation stores placeholder selector records. |
| `get_pipeline_selectors(pipeline_id)` | Get selector IDs for a pipeline. Returns `list[str]`. |
| `set_subscriptions(pipeline_id, subscription_ids)` | Replace pipeline's subscription associations (for `scope=selected`). |
| `get_pipeline_subscriptions(pipeline_id)` | Get subscription IDs for a pipeline. Returns `list[str]`. |

### Schema Mapping

The repository maps between model fields and DB columns:

- Model `playlist_id` ↔ DB `destination_playlist_id`
- Model `order` ↔ DB `sort_order`
- Model `enabled` (bool) ↔ DB `enabled` (INTEGER 0/1)
- Model `duration_min_seconds`, `duration_max_seconds` — `None` stored as `0` in DB, read back as `None` if `0`

### Cascade Delete Behavior

When a pipeline is deleted, SQLite's `ON DELETE CASCADE` automatically removes:
- All `pipeline_ignore_lists` entries for that pipeline
- All `pipeline_selectors` entries for that pipeline
- All `pipeline_subscriptions` entries for that pipeline

This is verified by unit tests and requires `PRAGMA foreign_keys = ON` (set by `connection.init_db`).

## Config Repository (`config.py`)

The config repository manages the `app_config` key-value store for runtime configuration.

### Operations

| Function | Purpose |
|----------|---------|
| `get_config()` | Get all config key-value pairs. Returns `dict[str, str]`. |
| `set_config(key, value)` | Set a config key-value pair. Uses `ON CONFLICT(key) DO UPDATE` for upsert. |
| `get_config_value(key, default=None)` | Get a single config value. Returns `default` if key doesn't exist. |

### Usage

Used for storing runtime configuration like schedule, reprocess_days, activity_limit, etc. All values are stored as strings; type conversion is the caller's responsibility.

## Videos Repository (`videos.py`)

The videos repository manages the `videos` audit trail table.

### Operations

| Function | Purpose |
|----------|---------|
| `insert_video(video: Video)` | Insert a video into the audit trail. Auto-sets `inserted_at` to `datetime('now')`. |
| `get_video(video_id)` | Get a video by its YouTube video_id (most recent insert). Returns `Video | None`. |
| `video_exists(video_id, pipeline_id)` | Check if a video has already been inserted for a pipeline. Returns `bool`. |
| `search_videos(video_id)` | Search for all insertions of a video. Returns `list[dict]` (not `Video` objects, since schema doesn't fully match model). |

### Schema Constraints

The `videos` table has `video_id` as PRIMARY KEY, which means each video can only be inserted once (not once per pipeline). This is the audit trail design — it tracks that a video was inserted, not all the places it was inserted.

## Runs Repository (`runs.py`)

The runs repository manages the `pipeline_runs` and `run_decisions` tables for run history and per-video decisions.

### Operations

| Function | Purpose |
|----------|---------|
| `create_run(run_summary: RunSummary)` | Create a new run record. Returns the run ID (`int`). |
| `update_run(run_id, updates: dict)` | Partial update of a run record. Accepts any field names as dict keys. |
| `get_run(run_id)` | Get a run by ID. Returns `RunSummaryResponse | None`. |
| `list_runs(limit=50)` | List recent runs, ordered by `started_at DESC`. Returns `list[RunSummaryResponse]`. |
| `add_decisions(run_id, decisions: list[dict])` | Batch insert run decisions. Each decision must have `video_id` and `action`. |
| `get_decisions(run_id, limit=500)` | Get decisions for a run, ordered by `id`. Returns `list[RunDecisionResponse]`. |

### Schema Mapping

The repository maps between model fields and DB columns:

- Model `completed_at` ↔ DB `finished_at`
- Model `subscriptions_fetched` ↔ DB `subscriptions_processed`
- Model `activities_collected` ↔ DB `videos_collected`
- Model `videos_enriched` ↔ DB `videos_after_cheap_filters`

## Subscriptions Repository (`subscriptions.py`)

The subscriptions repository manages the `subscriptions` table and `subscription_tracking` watermark table.

### Operations

| Function | Purpose |
|----------|---------|
| `upsert_subscriptions(subs: list[Subscription])` | Batch upsert subscriptions. Uses `ON CONFLICT(id) DO UPDATE` for idempotency. |
| `list_subscriptions()` | List all subscriptions, ordered by `title`. Returns `list[Subscription]`. |
| `get_subscription_stats()` | Get subscription statistics. Returns `dict` with `count`. |
| `update_tracking(subscription_id, last_fetched_at)` | Update subscription tracking watermark. Uses `ON CONFLICT(subscription_id) DO UPDATE`. |
| `get_tracking(subscription_id)` | Get tracking data for a subscription. Returns `dict | None` with `last_fetched_at`. |

### Schema Notes

The `subscriptions` table does not have a `thumbnail_url` column in the schema, so the repository returns `None` for that field in the `Subscription` model.

## OAuth Credential Migration

The `OAuthManager` in `src/sortarr/core/auth.py` includes a `migrate_from_pickle(pickle_path)` method that migrates credentials from a legacy pickle file to the database.

### Migration Behavior

- Returns `True` if migration happened, `False` if no pickle found or DB already has credentials
- Skips migration if `is_authenticated()` returns `True` (DB already has credentials)
- Logs a warning on successful migration
- Does NOT delete the pickle file (user must remove manually)
- Handles corrupt pickle files gracefully (logs error, returns `False`)

### Usage

Call `oauth_manager.migrate_from_pickle()` once at application startup to handle legacy deployments.
