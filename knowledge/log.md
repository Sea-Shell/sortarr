---
type: Changelog
title: Sortarr Knowledge Bundle — Change Log
description: Chronological record of changes to the knowledge/ OKF bundle. Append one line per change; newest at top.
resource: https://github.com/Sea-Shell/sortarr
tags: [sortarr, log, okf, changelog]
timestamp: 2026-07-13T15:00:00Z
---

# Change Log

Append a one-line entry whenever you add, edit, or remove a concept doc.
Format: `- YYYY-MM-DD — <doc(s) touched> — <what changed and why>`

- 2026-07-13 — auth.md — added automatic scope migration in get_credentials() to detect v1→v2 scope changes (4 scopes → 1 scope) and clear old credentials, forcing user re-authentication. Prevents OAuth token exchange errors from scope mismatches.

- 2026-07-13 — api.md, dev-workflow.md — implemented Prometheus metrics endpoint (GET /metrics) with sortarr_runs_total, sortarr_quota_used_today, sortarr_videos_inserted_total, sortarr_run_duration_seconds; metrics recorded by runner.py at end of each run. Documented entry point (__main__.py) with CLI args (--host, --port, --log-level), graceful shutdown handlers (SIGTERM/SIGINT), and startup flow.

- 2026-07-13 — api.md — implemented run management, preview, subscriptions, and stats routes: POST /api/run (trigger live run, 201 on success, 409 if run already active), GET /api/runs (list run history with ?limit=50), GET /api/runs/{id} (get run detail), GET /api/runs/{id}/decisions (get decisions for run with ?limit=500), POST /api/preview/mock (mock preview with synthetic activities, zero quota cost), POST /api/preview/cache (cache preview using activity_cache, zero quota cost), GET /api/subscriptions (list subscriptions from DB), GET /api/subscriptions/stats (per-subscription activity counts and last_fetched_at), GET /api/playlists (fetch user's YouTube playlists, requires auth, 1 quota unit), GET /api/stats (dashboard statistics: pipeline counts, subscription counts, activity cache size, run counts by status).

- 2026-07-13 — api.md — implemented full pipeline CRUD routes: GET /api/pipelines (list all), GET /api/pipelines/{id} (get one), POST /api/pipelines (create with junction tables), PUT /api/pipelines/{id} (partial update), DELETE /api/pipelines/{id} (cascade delete), PUT /api/pipelines/reorder (reorder), PUT /api/pipelines/{id}/ignore-lists (set ignore lists), PUT /api/pipelines/{id}/selectors (set selectors - 501), PUT /api/pipelines/{id}/subscriptions (set subscriptions); added ReorderRequest and SetJunctionRequest models.

- 2026-07-13 — api.md — implemented health and config routes: GET /api/health (status, auth state, next scheduled run, counts, quota), GET/PUT /api/config (runtime config with partial updates and scheduler rescheduling).

- 2026-07-13 — api.md — updated auth.py route table to reflect OAuth 2.0 flow (GET /auth/login → redirect, GET /auth/callback → exchange code, GET /auth/status → check auth state, POST /auth/logout → clear credentials); removed outdated device/poll endpoints.

- 2026-07-13 — api.md — documented FastAPI lifespan context manager (startup: init DB, reset quota, migrate pickle, create OAuth/YouTube/Runner, start scheduler; shutdown: stop scheduler, close DB), AppState container, and dependency injection functions (get_state, get_oauth_manager, require_youtube, get_runner).

- 2026-07-13 — scheduler.md — added Implementation section documenting PipelineScheduler class (init, start, stop, update_schedule, get_next_run_time), misfire grace time (3600s), and FastAPI lifespan integration.

- 2026-07-12 — pipeline.md — added Preview Modes section documenting mock preview (generates synthetic test activities per filter rule + baseline) and cache preview (runs filters on cached data), both with zero quota cost. Includes implementation details, mock types, acceptance criteria, and API endpoints.
- 2026-07-12 — pipeline.md — rewrote for v2 Runner: documented 8-step run flow (startup cleanup, concurrency guard, subscription/activity fetching, cheap filters, batch enrichment, duration filters, inserts, watermarks, cache pruning), quota guard thresholds, error handling, and quota budget.
- 2026-07-12 — database.md — added Config, Videos, Runs, and Subscriptions repository sections documenting all CRUD operations, schema mappings, and OAuth credential migration from pickle to DB.
- 2026-07-12 — database.md — added Pipelines Repository section documenting pipelines.py operations (create_pipeline, get_pipeline, list_pipelines, update_pipeline, delete_pipeline, reorder_pipelines), junction table helpers (set/get ignore_lists, selectors, subscriptions), schema mapping (playlist_id ↔ destination_playlist_id), and cascade delete behavior.

- 2026-07-12 — database.md — added Activity Cache Repository section documenting activities.py operations (upsert_activities, get_activities, get_cached_duration, update_duration, prune_old_entries, get_cache_stats), schema mapping (activity_type ↔ video_type), and idempotency guarantee.
- 2026-07-12 — auth.md — updated for DB-backed OAuth credentials (token_json in oauth_credentials table), removed pickle file references, documented OAuthManager flow with auto-refresh.
- 2026-07-12 — api.md — added YouTube API Client section documenting YouTubeAPIClient contract, methods, quota tracking, token refresh, and testing.
- 2026-06-24 — bundle created — initial OKF bundle: architecture, runtime-config, pipeline, filters, database, api, auth, scheduler, dev-workflow.
- 2026-06-24 — api.md, database.md — updated for sort_order column, reorder_pipelines function, ReorderRequest model, PUT /pipelines/reorder endpoint.
- 2026-07-08 — index.md, DESIGN.md — added DESIGN.md with responsive design system tokens, fluid typography, component inventory, and mobile-first layout rules. Direction B (Fluid Grid) confirmed by user.
- 2026-07-08 — pipeline.md — documented in-memory dedup by video_id in _collect_activities() to avoid redundant API calls.
- 2026-07-09 — api.md — updated subscriptions endpoint to DB-backed; added pipeline/runs/search route to route table; fixed route ordering note (literal paths before dynamic params).
- 2026-07-11 — api.md — added playlists route with YouTube API + DB fallback to route table.
- 2026-07-11 — api.md — enriched playlists fallback to also query distinct destination_playlist from pipelines table.
- 2026-07-11 — pipeline.md — added Subscription Sync section documenting DB persistence of subscriptions before Phase 1.
- 2026-07-11 — api.md — updated subscriptions endpoint to sync-then-serve pattern (YouTube API → DB fallback).
- 2026-07-12 — pipeline.md — documented restored per-subscription tracking narrowing in _compute_published_after (max() of reprocess_days ceiling and min_tracking_ts).
- 2026-07-12 — api.md — activity endpoint now falls back to activity_cache when YouTube API is unavailable.
- 2026-07-12 — architecture.md, index.md — v2 greenfield skeleton: deleted all v1 files, created new module layout with stubs. Added v1→v2 diff table and updated flow descriptions.
- 2026-07-12 — runtime-config.md — v2 Settings fields: removed v1 fields (pickle_file, credentials_file, log_file, compare_distance, playlist_sleep, etc.), added client_secret_path, public_url as env var. Added v1→v2 changelog section.
- 2026-07-12 — database.md — rewrote for v2: replaced v1 schema (channel, playlist, routing_rules, etc.) with v2 schema (14 tables, 6 indexes, V3_SCHEMA_SQL). Added init_db() description and repository layout.
- 2026-07-12 — database.md — added connection lifecycle (init_db/get_connection/close_db/connection_ctx), WAL mode, foreign keys, and pragma table.
- 2026-07-12 — filters.md — added duration filter to filter table, documented two-stage filter chain (cheap → duration), and described check_duration behavior (unknown durations pass through).
