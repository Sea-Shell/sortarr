---
type: Component
title: Sortarr Scheduler
description: APScheduler-based internal scheduling that runs the pipeline and playlist tracker on cron expressions, replacing an external Kubernetes CronJob.
resource: https://github.com/Sea-Shell/sortarr/blob/main/src/sortarr/core/scheduler.py
tags: [sortarr, scheduler, cron, apscheduler]
timestamp: 2026-06-24T10:00:00Z
---

# What it does

The app runs an **internal scheduler (APScheduler)** started with the app
process (`core/scheduler.py`, wired in the [`lifespan()`](/knowledge/concepts/api.md)).
No separate Kubernetes CronJob is needed — a legacy `kubernetes-manifests/cronjob.yaml`
exists but is **superseded** by this internal scheduler.

# Schedules

| Job              | Env var                     | Default cron  | Meaning          |
| ---------------- | --------------------------- | ------------- | ---------------- |
| Pipeline run     | `SORTARR_SCHEDULE`          | `0 */6 * * *` | Every 6 hours    |
| Playlist tracker | `playlist_tracker_schedule` | `0 3 * * *`   | Nightly at 03:00 |

See [runtime config](/knowledge/concepts/runtime-config.md) for the settings.

# Manual vs automatic

A scheduled run and a manual `POST /api/pipeline/trigger` invoke the **same**
core path ([`PipelineOrchestrator`](/knowledge/concepts/pipeline.md) via
`pipeline_runner`) — shared logic for DRYness and consistent behavior.

# Concurrency

`SORTARR_PIPELINE_CONCURRENCY` (1–10, default 1) bounds parallel pipeline
execution within a run. Rate-limit knobs `playlist_sleep` and
`subscription_sleep` space out API calls to stay within YouTube quota.
