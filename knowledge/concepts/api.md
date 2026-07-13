---
type: HTTP API
title: Sortarr HTTP API
description: FastAPI app factory, shared AppState, dependency providers, and the REST routes for config, auth, pipelines, subscriptions, and metrics.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr/api
tags: [sortarr, api, fastapi, rest]
timestamp: 2026-07-13T09:00:00Z
---

# App factory

`src/sortarr/api/app.py` exposes `create_app()` which builds the FastAPI app with
a `lifespan()` async context manager. The lifespan:

**Startup:**
1. Initializes database connection and applies schema
2. Resets quota counter to 0
3. Migrates OAuth credentials from pickle file if needed
4. Creates OAuth manager and YouTube client (if authenticated)
5. Creates Runner (if YouTube client available)
6. Starts scheduler with cron-based callback

**Shutdown:**
1. Stops scheduler
2. Closes database connection

Shared state lives in `AppState` (settings, OAuth manager, YouTube client, Runner,
scheduler) and is reached in handlers via `deps.py`:

- `get_state(request)` — returns the `AppState`
- `get_oauth_manager(state)` — returns OAuth manager (500 if not initialized)
- `require_youtube(state)` — dependency that 401s if not authenticated
- `get_runner(state)` — returns Runner (503 if not initialized)

CORS middleware allows all origins for local dev.

Served by `uvicorn` on `SORTARR_API_PORT` (default 8080). Web UI at `/ui`.

# Routes

Route modules in `src/sortarr/api/routes/`:

| Module                | Endpoints (summary)                                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `health.py`           | `GET /api/health`                                                                                                |
| `config.py`           | `GET/PUT /api/config`, `GET/POST /api/config/ignores`, `DELETE /api/config/ignores/{id}`                         |
| `auth.py`             | `GET /api/auth/login` (redirect to Google OAuth), `GET /api/auth/callback` (exchange code), `GET /api/auth/status` (check auth state), `POST /api/auth/logout` (clear credentials) — see [auth](/knowledge/concepts/auth.md) |
| `subscriptions.py`    | `GET /api/subscriptions` (syncs from YouTube API when available, falls back to DB cache), `GET /api/subscriptions/{cid}/activity` (YouTube API → activity_cache fallback) |
| `rules.py`            | CRUD `/api/rules` (legacy routing rules)                                                                         |
| `pipelines.py`        | CRUD pipelines, selectors, attachments, ignore-lists CRUD, `GET /api/playlists` (YouTube API with DB fallback from `playlist` + `pipelines` tables) |
| `pipeline.py`         | `POST /api/pipeline/trigger`, `GET /api/pipeline/runs`, `GET /api/pipeline/runs/search`, `GET /api/pipeline/runs/{id}`, `GET /api/pipeline/runs/{id}/decisions` |
| `playlist_tracker.py` | Playlist reconciliation endpoints                                                                                |
| `stats.py`            | Aggregate stats                                                                                                  |
| (root)                | `GET /metrics` — Prometheus                                                                                      |

# Triggering a run

`POST /api/pipeline/trigger` runs the **same** logic as the
[scheduler](/knowledge/concepts/scheduler.md), via `pipeline_runner.execute_pipeline`,
which constructs a [`PipelineOrchestrator`](/knowledge/concepts/pipeline.md) and
persists results to `pipeline_runs` in the [database](/knowledge/concepts/database.md).

# Models

Request/response models are pydantic (`api/models.py` and `models/`):
`HealthResponse`, `PipelineCreate/Update/Response`, `ReorderRequest`,
`IgnoreList*`, `PipelineRunResponse`, etc.

### Pipeline Reorder API

`PUT /api/pipelines/reorder` accepts `ReorderRequest { pipeline_ids: list[str] }`
and assigns sequential `sort_order` (0, 1, 2, ...) based on position in the list.
The handler validates the list is non-empty and returns 400 if empty, 500 on DB
failure. This replaced the previous swap-based `orders` dict API to fix the
issue where all pipelines had `sort_order=0` and swapping was a no-op.

# YouTube API Client

`src/sortarr/core/youtube.py` provides `YouTubeAPIClient`, a wrapper around
`google-api-python-client` with quota tracking and token refresh support.

## Contract

All methods accept an `http` parameter (`google.auth.transport.requests.AuthorizedSession`)
for OAuth token refresh. No global credentials state.

Module-level quota tracking:
- `get_quota_used()` → current quota usage (int)
- `reset_quota()` → reset counter to 0 (called at midnight PT or app restart)
- Internal `_increment_quota(cost)` → increments counter

## Methods

| Method | Quota Cost | Purpose |
|--------|-----------|---------|
| `get_subscriptions(http, page_token?, max_results=50)` | 1 | Fetch user's subscriptions |
| `get_activities(http, channel_id, published_after, page_token?, max_results=50)` | 1 | Fetch channel activities |
| `get_videos_batch(http, video_ids_csv)` | 1 | Fetch video details (max 50 IDs) |
| `get_playlists(http, max_results=50)` | 1 | Fetch user's playlists |
| `insert_playlist_item(http, playlist_id, video_id)` | 50 | Insert video into playlist |
| `get_playlist_items(http, playlist_id, page_token?, max_results=50)` | 1 | Fetch playlist items |

All methods return `dict[str, Any]` — raw YouTube API JSON response.

## Quota tracking

The module-level `_quota_used` counter increments on every API call:
- Most read operations: 1 unit
- `insert_playlist_item`: 50 units (dominant cost)

The counter is reset at midnight PT (via scheduler) or on app restart. The 10,000
units/day hard ceiling is enforced at the runner level, not in the client.

## Token refresh

The `http` parameter is an `AuthorizedSession` that automatically refreshes expired
OAuth tokens. The client does NOT manage credentials — that's handled by
`sortarr.core.auth` (see [auth](/knowledge/concepts/auth.md)).

## Testing

Comprehensive unit tests in `tests/test_youtube.py` mock `googleapiclient.discovery.build`
to verify:
- Correct API endpoint calls (part, parameters)
- Quota counter increments correctly
- Pagination support (page_token)
- All methods return expected structure
