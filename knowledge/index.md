---
type: Bundle Index
title: Sortarr Knowledge Bundle
description: Root index for the sortarr OKF knowledge bundle. Start here, then follow links into concepts/ one level at a time.
resource: https://github.com/Sea-Shell/sortarr
tags: [sortarr, index, okf]
timestamp: 2026-07-12T12:00:00Z
---

# Sortarr Knowledge Bundle

`sortarr` (package `sortarr`, formerly `ys2wl`) is a Python 3.13 web service
that scrapes YouTube subscriptions and routes new videos into playlists based on
configurable per-pipeline rules. Built on **FastAPI + uvicorn**, scheduled with
**APScheduler**, persisted in **SQLite**, authenticated via **Google OAuth**.

This bundle is an [OKF](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf)
knowledge base: a directory of markdown files an agent can navigate selectively
instead of re-reading the codebase each session.

# Concepts

See [concepts/](/knowledge/concepts/index.md) for the full list. Quick links:

- [Architecture](/knowledge/concepts/architecture.md) — v2 module layout, request/run flow, and v1→v2 diff
- [Runtime Configuration](/knowledge/concepts/runtime-config.md) — `SORTARR_*` env vars + DB-backed config
- [Pipeline](/knowledge/concepts/pipeline.md) — the runner that routes videos via cheap filters → shared enrichment → duration filters
- [Filters](/knowledge/concepts/filters.md) — word, ignore-list, title-similarity, selector, db-exists, duration
- [Database](/knowledge/concepts/database.md) — SQLite WAL schema, migrations, repository layer
- [HTTP API](/knowledge/concepts/api.md) — FastAPI app factory, routes, dependencies
- [Auth](/knowledge/concepts/auth.md) — Google OAuth device + browser flow
- [Scheduler](/knowledge/concepts/scheduler.md) — APScheduler cron-driven runs
- [Dev Workflow](/knowledge/concepts/dev-workflow.md) — build, test, lint, Docker, K8s
