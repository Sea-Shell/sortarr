---
type: HTTP API
title: Sortarr HTTP API
description: FastAPI app factory, shared AppState, dependency providers, and the REST routes for config, auth, pipelines, subscriptions, and metrics.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr/api
tags: [sortarr, api, fastapi, rest]
timestamp: 2026-06-24T12:00:00Z
---

# App factory

`src/sortarr/api/app.py` exposes `create_app()` which builds the FastAPI app and
a `lifespan()` context. Shared state lives in `AppState` (settings, DB
`Connection`, `YouTubeAPIClient`, scheduler) and is reached in handlers via
`deps.py`:

- `get_state()` — returns the `AppState`
- `require_youtube()` — dependency that 401/409s if not authenticated

Served by `uvicorn` on `SORTARR_API_PORT` (default 8080). Web UI at `/ui`.

# Routes

Route modules in `src/sortarr/api/routes/`:

| Module                | Endpoints (summary)                                                                                              |
| --------------------- | ---------------------------------------------------------------------------------------------------------------- |
| `health.py`           | `GET /api/health`                                                                                                |
| `config.py`           | `GET/PUT /api/config`, `GET/POST /api/config/ignores`, `DELETE /api/config/ignores/{id}`                         |
| `auth.py`             | `GET /api/auth/status`, `POST /api/auth/device`, `POST /api/auth/poll` — see [auth](/knowledge/concepts/auth.md) |
| `subscriptions.py`    | `GET /api/subscriptions`, `GET /api/subscriptions/{cid}/activity`                                                |
| `rules.py`            | CRUD `/api/rules` (legacy routing rules)                                                                         |
| `pipelines.py`        | CRUD pipelines, selectors, attachments                                                                           |
| `pipeline.py`         | `POST /api/pipeline/trigger`, `GET /api/pipeline/runs`, `GET /api/pipeline/runs/{id}`                            |
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
