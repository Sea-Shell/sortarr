---
type: Architecture
title: Sortarr Architecture
description: Module layout of src/sortarr v2, the core abstractions, and how a pipeline run and an HTTP request flow through the system.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr
tags: [sortarr, architecture, overview]
timestamp: 2026-07-12T12:00:00Z
---

# Module Layout (v2 — greenfield redesign)

```
src/sortarr/
├── __init__.py          # __version__ = "2.0.0"
├── __main__.py          # entry point: `python -m sortarr` → main()
├── config.py            # Settings (pydantic-settings, env_prefix SORTARR_)
├── metrics.py           # Prometheus metrics
├── api/                 # FastAPI app, routes, dependencies  → see api.md
│   ├── app.py           # create_app(), lifespan(), AppState
│   ├── deps.py          # get_state(), require_youtube()
│   ├── models.py        # API request/response models
│   └── routes/          # auth, config, health, pipeline, pipelines,
│                        #   preview, stats, subscriptions
├── core/                # business logic
│   ├── runner.py        # pipeline run execution, run_active lock, crash recovery
│   ├── preview.py       # mock and cached preview logic (zero quota)
│   ├── filters.py       # filter chain orchestration
│   ├── enricher.py      # batch video metadata enrichment (shared quota)
│   ├── scheduler.py     # APScheduler wiring  → see scheduler.md
│   ├── auth.py          # OAuth flow          → see auth.md
│   └── youtube.py       # YouTube Data API v3 client
├── db/                  # persistence          → see database.md
│   ├── connection.py    # SQLite connection management (WAL mode)
│   ├── migrations.py    # schema migrations, auto-run on startup
│   └── repository/      # config, pipelines, activities, videos, runs, subscriptions
├── filters/             # per-pipeline routing filters  → see filters.md
│   ├── word_filter.py
│   ├── ignore_list.py
│   ├── title_similarity.py
│   ├── selector_filter.py
│   ├── db_exists.py
│   └── duration_filter.py
└── models/              # pydantic: pipeline.py, youtube.py
    ├── pipeline.py      # Pipeline, RunDecision, RunResult
    └── youtube.py       # Channel, Subscription, Activity, Video
```

# Key Differences from v1

| v1                          | v2                                           |
| --------------------------- | -------------------------------------------- |
| `core/pipeline.py`          | Removed — logic moved to `core/runner.py`    |
| `core/pipeline_runner.py`   | Merged into `core/runner.py`                 |
| `core/playlist_tracker.py`  | Removed (deferred)                           |
| `core/utils.py`             | Removed — no longer needed                   |
| `api/routes/rules.py`       | Removed — pipelines CRUD replaces it         |
| `api/routes/playlist_tracker.py` | Removed (deferred)                      |
| `db/repository/ignore_lists.py` | Merged into pipeline/repository pattern  |
| `db/repository/pipeline.py`     | Renamed to `db/repository/pipelines.py` |
| `db/repository/pipeline_runs.py`| Renamed to `db/repository/runs.py`      |
| —                           | `core/preview.py` (new: mock + cached preview) |
| —                           | `core/enricher.py` (new: batch enrichment)   |
| —                           | `filters/db_exists.py` (new)                 |
| —                           | `filters/duration_filter.py` (new)           |
| —                           | `db/repository/activities.py` (new)          |
| —                           | `db/repository/subscriptions.py` (new)       |

# Core Abstractions

| Abstraction     | Role                                                                |
| --------------- | ------------------------------------------------------------------- |
| `runner.py`     | Drives a full routing run — cheap filters → shared enrichment → duration filters → insert  → see [pipeline](/knowledge/concepts/pipeline.md) |
| `preview.py`    | Mock + cached dry-run preview (zero YouTube quota)                  |
| `enricher.py`   | Batch `videos.list` calls to share quota across pipelines           |
| `Connection`    | SQLite connection with WAL mode                                     |
| `YouTubeAPIClient` | YouTube Data API v3 calls                                      |

# Flow: A Pipeline Run (v2)

1. [Scheduler](/knowledge/concepts/scheduler.md) (or manual trigger) acquires `run_active` lock → starts a run.
2. `runner.py` fetches subscriptions via YouTube API, caches in [DB](/knowledge/concepts/database.md).
3. For each enabled pipeline: cheap [filters](/knowledge/concepts/filters.md) run (word, ignore, db_exists, title_similarity, selectors).
4. `enricher.py` batch-deduplicates survivor IDs and calls `videos.list` once (shared quota).
5. Duration filters run per-pipeline on enriched metadata.
6. Surviving videos inserted into destination playlists.
7. Results persist to `pipeline_runs`; lock released.

# Flow: An HTTP Request (v2)

`uvicorn` → FastAPI app from [`create_app()`](/knowledge/concepts/api.md) → route
handler → reads shared `AppState` (settings, DB connection, YouTube client) via
`deps.py` → repository call against [SQLite](/knowledge/concepts/database.md).

# Note on naming

The package was renamed from `ys2wl` to `sortarr`. Older graphify cache entries
and a legacy K8s CronJob manifest still reference `ys2wl` paths; current source
lives under `src/sortarr/`.
