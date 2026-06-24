---
type: Service Configuration
title: Sortarr Runtime Configuration
description: SORTARR_* environment variables, the pydantic Settings model, and how DB-backed runtime config relates to env seeding.
resource: https://github.com/Sea-Shell/sortarr/blob/main/src/sortarr/config.py
tags: [sortarr, config, settings, env]
timestamp: 2026-06-24T10:00:00Z
---

# Two-tier config

1. **Env vars** (`SORTARR_*`) are read by `Settings` (pydantic-settings,
   `env_prefix="SORTARR_"`, also reads `.env`). They **seed the DB on first run**.
2. **Runtime config** lives in the [SQLite DB](/knowledge/concepts/database.md) and
   is edited via the web UI at `/ui#config` or the
   [`/api/config`](/knowledge/concepts/api.md) endpoint.

> Gotcha: because env vars only _seed_, changing one after the DB exists has no
> effect. Edit runtime config through the DB/API instead.

# Settings fields

Defined in `src/sortarr/config.py` as `Settings(BaseSettings)`:

| Env var                        | Field                       | Default                 | Notes                                                                            |
| ------------------------------ | --------------------------- | ----------------------- | -------------------------------------------------------------------------------- |
| `SORTARR_API_PORT`             | `api_port`                  | `8080`                  | HTTP listen port                                                                 |
| `SORTARR_LOG_LEVEL`            | `log_level`                 | `warning`               |                                                                                  |
| `SORTARR_LOG_FILE`             | `log_file`                  | `stream`                | `stream` = stdout                                                                |
| `SORTARR_DATABASE_FILE`        | `database_file`             | `sortarr.db`            | SQLite path                                                                      |
| `SORTARR_PICKLE_FILE`          | `pickle_file`               | `credentials.pickle`    | OAuth token — see [auth](/knowledge/concepts/auth.md)                            |
| `SORTARR_CREDENTIALS_FILE`     | `credentials_file`          | `client_secret.json`    | Google OAuth client JSON                                                         |
| `SORTARR_SCHEDULE`             | `schedule`                  | `0 */6 * * *`           | Pipeline cron — see [scheduler](/knowledge/concepts/scheduler.md)                |
| `SORTARR_COMPARE_DISTANCE`     | `compare_distance`          | `80`                    | Title similarity threshold 0–100 — see [filters](/knowledge/concepts/filters.md) |
| `SORTARR_REPROCESS_DAYS`       | `reprocess_days`            | `2`                     | Days before re-checking a sub                                                    |
| `SORTARR_PLAYLIST_SLEEP`       | `playlist_sleep`            | `10`                    | Seconds between playlist inserts                                                 |
| `SORTARR_SUBSCRIPTION_SLEEP`   | `subscription_sleep`        | `30`                    | Seconds between subs                                                             |
| `SORTARR_PIPELINE_CONCURRENCY` | `pipeline_concurrency`      | `1`                     | 1–10 parallel pipelines                                                          |
| `SORTARR_ACTIVITY_LIMIT`       | `activity_limit`            | `0`                     | Max activities/sub (0=∞)                                                         |
| `SORTARR_SUBSCRIPTION_LIMIT`   | `subscription_limit`        | `0`                     | Max subs/run (0=∞)                                                               |
| `SORTARR_PUBLISHED_AFTER`      | `published_after`           | —                       | ISO8601 lower bound                                                              |
| `SORTARR_NO_WEBBROWSER`        | `no_webbrowser`             | `false`                 | Headless auth                                                                    |
| (n/a)                          | `public_url`                | `http://localhost:8080` | Used in OAuth redirects                                                          |
| (n/a)                          | `playlist_tracker_schedule` | `0 3 * * *`             | Nightly tracker cron                                                             |

# Validation

Some fields are range-constrained at the pydantic level: `compare_distance`
0–100, `pipeline_concurrency` 1–10, several `ge=0` counters. Out-of-range env
values fail fast at startup.
