---
type: Datastore
title: Sortarr Database
description: SQLite persistence — connection handling, auto-run migrations, the table schema, and the repository layer that wraps all queries.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr/db
tags: [sortarr, database, sqlite, persistence]
timestamp: 2026-06-24T10:00:00Z
---

# Layout

```
src/sortarr/db/
├── connection.py   # opens the sqlite3 Connection (god node, 56 edges)
├── migrations.py   # schema DDL, auto-run on startup
└── repository/
    ├── config.py        # runtime config key/values
    ├── ignore_lists.py  # ignore lists + entries  → see filters.md
    ├── pipeline.py      # pipelines, selectors, tracking, list attachments
    ├── pipeline_runs.py # run history + decisions
    └── videos.py        # activity cache + routed-video records
```

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

Pipelines, selectors, ignore lists, and pipeline↔subscription/ignore-list
attachments are managed through the `pipeline` and `ignore_lists` repositories.

# Repository pattern

Handlers and the [pipeline](/knowledge/concepts/pipeline.md) never write SQL
inline — they call functions in `repository/` (e.g. `videos.cache_activity`,
`pipeline.get_pipeline_tracking`, `pipeline.get_pipeline_selectors`). The
`Connection` is created once and shared through
[`AppState`](/knowledge/concepts/api.md).
