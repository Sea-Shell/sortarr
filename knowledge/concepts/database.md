---
type: Datastore
title: Sortarr Database
description: SQLite persistence — connection handling with WAL mode and foreign keys, auto-run migrations, the table schema, and the repository layer that wraps all queries.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr/db
tags: [sortarr, database, sqlite, persistence, wal, foreign-keys]
timestamp: 2026-07-12T12:00:00Z
---

# Layout

```
src/sortarr/db/
├── connection.py   # SQLite connection management (WAL mode, foreign keys)
├── migrations.py   # schema DDL, auto-run on startup
└── repository/
    ├── config.py        # runtime config key/values
    ├── ignore_lists.py  # ignore lists + entries  → see filters.md
    ├── pipeline.py      # pipelines, selectors, tracking, list attachments
    ├── pipeline_runs.py # run history + decisions
    └── videos.py        # activity cache + routed-video records
```

# Connection lifecycle

`connection.py` manages a single module-level `sqlite3.Connection` with
three functions called from the [FastAPI lifespan](/knowledge/concepts/api.md):

| Function       | When called        | What it does                                        |
| -------------- | ------------------ | --------------------------------------------------- |
| `init_db(path)` | App startup        | Opens connection, sets WAL mode + foreign keys + busy timeout |
| `get_connection()` | Any time       | Returns the connection; raises `RuntimeError` if not initialized |
| `close_db()`    | App shutdown       | Closes the connection cleanly                       |

A `connection_ctx()` context manager provides transactional semantics:
commit on success, rollback on exception.

# Pragmas

| Pragma               | Value  | Why                                                          |
| -------------------- | ------ | ------------------------------------------------------------ |
| `journal_mode`       | `WAL`  | Concurrent readers during writes; better throughput           |
| `foreign_keys`       | `ON`   | Enforces referential integrity (off by default in sqlite3)   |
| `busy_timeout`       | `5000` | Wait up to 5 seconds on lock contention before failing       |
| `row_factory`        | `sqlite3.Row` | Dict-like column access (`row["title"]`) instead of positional |

WAL mode requires a file-backed database — `:memory:` databases always use the
`memory` journal and silently ignore the WAL pragma.

The DB path is `SORTARR_DATABASE_FILE` (default `sortarr.db`) — see
[runtime config](/knowledge/concepts/runtime-config.md).

# Migrations

`migrations.py` defines the schema as SQL (`V1_SCHEMA_SQL`, …) and runs it on
startup; there is **no separate migrate command**. Tables use
`CREATE TABLE IF NOT EXISTS`, so startup is idempotent.

# Schema (V1 core tables)

| Table           | Purpose                                                                                                                                             |
| --------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `videos`        | `videoId` PK, title, `subscriptionId`, `playlistId`, `duration_seconds`, `route_rule` — activity cache + routed records                             |
| `channel`       | The authenticated user's channel (`id`, `title`)                                                                                                    |
| `playlist`      | Known playlists (`id`, `title`)                                                                                                                     |
| `subscription`  | Subscriptions (`id`, `title`, `timestamp`)                                                                                                          |
| `last_run`      | Last run timestamp                                                                                                                                  |
| `routing_rules` | Legacy rule rows: `priority`, `field`, `operator`, `pattern`, `destination_playlist_id`, `enabled`, `minimum_length`, `maximum_length`, `catch_all` |
| `pipeline_runs` | Run history (see `pipeline_runs` repository)                                                                                                        |

The `pipelines` table has a `sort_order INTEGER NOT NULL DEFAULT 0` column
(added in V9 migration). `get_pipelines()` orders by `sort_order ASC, name ASC`.
`reorder_pipelines(con, pipeline_ids: list[str])` assigns sequential sort_order
values (0, 1, 2, …) based on list position.

Pipelines, selectors, ignore lists, and pipeline↔subscription/ignore-list
attachments are managed through the `pipeline` and `ignore_lists` repositories.

# Repository pattern

Handlers and the [pipeline](/knowledge/concepts/pipeline.md) never write SQL
inline — they call functions in `repository/` (e.g. `videos.cache_activity`,
`pipeline.get_pipeline_tracking`, `pipeline.get_pipeline_selectors`). The
`Connection` is created once and shared through
[`AppState`](/knowledge/concepts/api.md).
