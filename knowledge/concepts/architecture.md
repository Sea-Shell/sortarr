---
type: Architecture
title: Sortarr Architecture
description: Module layout of src/sortarr, the core abstractions, and how a pipeline run and an HTTP request flow through the system.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr
tags: [sortarr, architecture, overview]
timestamp: 2026-06-24T10:00:00Z
---

# Module Layout

```
src/sortarr/
├── __main__.py        # entry point: `python -m sortarr` → main()
├── config.py          # Settings (pydantic-settings, env_prefix SORTARR_)
├── metrics.py         # Prometheus metrics
├── api/               # FastAPI app, routes, dependencies  → see api.md
│   ├── app.py         # create_app(), lifespan(), AppState
│   ├── deps.py        # get_state(), require_youtube()
│   └── routes/        # auth, config, health, pipeline, pipelines,
│                      #   playlist_tracker, rules, stats, subscriptions
├── core/              # business logic
│   ├── pipeline.py        # PipelineOrchestrator  → see pipeline.md
│   ├── pipeline_runner.py # execute a run, persist results
│   ├── scheduler.py       # APScheduler wiring   → see scheduler.md
│   ├── playlist_tracker.py# nightly playlist reconciliation
│   ├── auth.py            # OAuth flow           → see auth.md
│   ├── youtube.py         # YouTubeAPIClient (god node, 34 edges)
│   └── utils.py
├── db/                # persistence              → see database.md
│   ├── connection.py  # Connection (god node, 56 edges)
│   ├── migrations.py  # auto-run on startup
│   └── repository/    # config, ignore_lists, pipeline, pipeline_runs, videos
├── filters/           # routing filters          → see filters.md
└── models/            # pydantic: pipeline.py, youtube.py (Channel, Playlist, Activity)
```

# Core Abstractions

Per the graphify graph report, the most-connected ("god") nodes are:

| Abstraction            | Role                                                                        |
| ---------------------- | --------------------------------------------------------------------------- |
| `Connection` (sqlite3) | Threaded through nearly everything; the DB handle                           |
| `YouTubeAPIClient`     | All YouTube Data API calls live here                                        |
| `Activity`             | A discovered video (id, title, published_at, type)                          |
| `Channel` / `Playlist` | The authenticated user's own channel + target playlists                     |
| `PipelineOrchestrator` | Drives a full routing run — see [pipeline](/knowledge/concepts/pipeline.md) |

# Flow: A Pipeline Run

1. [Scheduler](/knowledge/concepts/scheduler.md) (or a manual trigger) starts a run.
2. [`PipelineOrchestrator`](/knowledge/concepts/pipeline.md) fetches subscriptions
   via `YouTubeAPIClient`, caches activities in the [DB](/knowledge/concepts/database.md).
3. Each enabled pipeline applies its [filters](/knowledge/concepts/filters.md) and
   routes surviving videos into a destination playlist.
4. Results persist to `pipeline_runs`; progress streams via an `on_progress` callback.

# Flow: An HTTP Request

`uvicorn` → FastAPI app from [`create_app()`](/knowledge/concepts/api.md) → route
handler → reads shared `AppState` (settings, DB `Connection`, YouTube client) via
`deps.py` → repository call against [SQLite](/knowledge/concepts/database.md).

# Note on naming

The package was renamed from `ys2wl` to `sortarr`. Older graphify cache entries
and a legacy K8s CronJob manifest still reference `ys2wl` paths; current source
lives under `src/sortarr/`.
