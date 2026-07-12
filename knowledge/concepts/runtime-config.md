---
type: Service Configuration
title: Sortarr Runtime Configuration
description: SORTARR_* environment variables, the pydantic Settings model, and how DB-backed runtime config relates to env seeding.
resource: https://github.com/Sea-Shell/sortarr/blob/main/src/sortarr/config.py
tags: [sortarr, config, settings, env]
timestamp: 2026-07-12T16:00:00Z
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

| Env var                    | Field                | Default                 | Notes                                                              |
| -------------------------- | -------------------- | ----------------------- | ------------------------------------------------------------------ |
| `SORTARR_SCHEDULE`         | `schedule`           | `0 */6 * * *`           | Pipeline cron — see [scheduler](/knowledge/concepts/scheduler.md)  |
| `SORTARR_REPROCESS_DAYS`   | `reprocess_days`     | `2`                     | Days before re-checking a sub                                      |
| `SORTARR_ACTIVITY_LIMIT`   | `activity_limit`     | `0`                     | Max activities/sub (0=∞)                                           |
| `SORTARR_SUBSCRIPTION_LIMIT` | `subscription_limit` | `0`                   | Max subs/run (0=∞)                                                 |
| `SORTARR_PUBLISHED_AFTER`  | `published_after`    | —                       | ISO8601 lower bound, overrides watermark                           |
| `SORTARR_PUBLIC_URL`       | `public_url`         | `http://localhost:8080` | Public-facing URL for OAuth callback                               |
| `SORTARR_CLIENT_SECRET_PATH` | `client_secret_path` | `client_secret.json`  | Path to Google OAuth client secret file                            |
| `SORTARR_DATABASE_FILE`    | `database_file`      | `sortarr.db`            | SQLite path                                                        |
| `SORTARR_LOG_LEVEL`        | `log_level`          | `warning`               |                                                                    |
| `SORTARR_API_PORT`         | `api_port`           | `8080`                  | HTTP listen port (legacy)                                          |

# Validation

Fields are unconstrained by default in v2. The `reprocess_days` and
`activity_limit`/`subscription_limit` fields accept `0` as "unlimited".
Out-of-range env values will fail fast at the pydantic level if validation
rules are added later.

# v1 → v2 changes

- Removed v1 fields: `pickle_file`, `credentials_file`, `log_file`,
  `compare_distance`, `playlist_sleep`, `subscription_sleep`,
  `pipeline_concurrency`, `no_webbrowser`, `playlist_tracker_schedule`.
- Added: `client_secret_path` (renamed from `credentials_file`), `public_url`
  (now an env var).
- `compare_distance` moved to pipeline-level config (per-pipeline selector
  threshold), no longer global.
