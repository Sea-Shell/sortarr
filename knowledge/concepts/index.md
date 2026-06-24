---
type: Directory Index
title: Sortarr Concepts
description: Index of all concept documents in the sortarr knowledge bundle, with one-line descriptions for progressive disclosure.
resource: https://github.com/Sea-Shell/sortarr
tags: [sortarr, index]
timestamp: 2026-06-24T10:00:00Z
---

# Concepts

| Concept                                                        | What it covers                                                    |
| -------------------------------------------------------------- | ----------------------------------------------------------------- |
| [Architecture](/knowledge/concepts/architecture.md)            | `src/sortarr/` module layout, core abstractions, run/request flow |
| [Runtime Configuration](/knowledge/concepts/runtime-config.md) | `SORTARR_*` env vars, `Settings`, DB-backed runtime config        |
| [Pipeline](/knowledge/concepts/pipeline.md)                    | `PipelineOrchestrator` two-phase routing logic                    |
| [Filters](/knowledge/concepts/filters.md)                      | word / selector / ignore-list / title-similarity filters          |
| [Database](/knowledge/concepts/database.md)                    | SQLite schema, auto-migrations, repository layer                  |
| [HTTP API](/knowledge/concepts/api.md)                         | FastAPI app factory, `AppState`, routes, deps                     |
| [Auth](/knowledge/concepts/auth.md)                            | Google OAuth credential flow and storage                          |
| [Scheduler](/knowledge/concepts/scheduler.md)                  | APScheduler cron schedules, manual triggers                       |
| [Dev Workflow](/knowledge/concepts/dev-workflow.md)            | uv, make targets, ruff, pytest, Docker, K8s                       |
