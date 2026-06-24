---
type: Process
title: Sortarr Pipeline Orchestrator
description: The two-phase PipelineOrchestrator that collects subscription activity then routes videos into playlists per pipeline, with skip rules.
resource: https://github.com/Sea-Shell/sortarr/blob/main/src/sortarr/core/pipeline.py
tags: [sortarr, pipeline, routing, core]
timestamp: 2026-06-24T10:00:00Z
---

# Overview

`PipelineOrchestrator` (`src/sortarr/core/pipeline.py`) executes a full routing
run. It is constructed with `Settings`, a `YouTubeAPIClient`, a DB `Connection`,
the user's `Channel`/`Playlist`, the list of `PipelineConfig`s, resolved ignore
lists, a default playlist, and an optional `dry_run` flag and `on_progress`
callback. Entry point is `_run()`, returning a `PipelineSummary`.

# Phase 1 — Data Collection

`_collect_activities(subscriptions)` fetches activity for **every** subscription
once via `youtube.get_subscription_activity(...)` and caches each `Activity` into
the [`videos` cache table](/knowledge/concepts/database.md). Returns
`{sub_id: [Activity]}`.

The lookback (`published_after`) is computed by `_compute_published_after`:

- use `settings.published_after` if set, else
- `now - reprocess_days` if `reprocess_days > 0`, else
- `now - 52 weeks`.

> Deliberately does **not** use per-subscription tracking here, to avoid
> prematurely narrowing the window when multiple pipelines share a subscription.
> The per-pipeline freshness check (Phase 2.2) handles reprocessing instead.

# Phase 2 — Per-Pipeline Processing

For each **enabled** `PipelineConfig`:

1. **Resolve ignore lists** attached to the pipeline, bucketed by type into
   `video` / `word` / `subscription` lists — see [filters](/knowledge/concepts/filters.md).
2. **Resolve selectors** (`PipelineSelector`: field, operator, pattern,
   combine_operator AND/OR).
3. **Determine scope**: `subscription_scope == "selected"` limits to attached
   subscription ids; otherwise all subscriptions.
4. For each target subscription, apply skip checks in order:
   - **2.1 Subscription ignore** — title in `ignore_subs` → skip (`reason="ignored"`).
   - **2.2 Reprocess window** — if `get_pipeline_tracking` shows it was checked
     within `reprocess_days`, skip (`reason="already_up_to_date"`).
   - Then per-video [filters](/knowledge/concepts/filters.md) decide routing.

Surviving videos are inserted into the destination playlist (rate-limited by
`playlist_sleep`); routed videos are recorded against `route_rule`.

# Outputs

A `PipelineSummary` accumulates `pipelines_invoked`, `subscriptions_skipped`,
`subscription_skips[]` (with reason/detail), errors, and timing. Progress is
streamed live through `on_progress(skip_or_result, summary)` for the UI. Results
persist to `pipeline_runs` via [`pipeline_runner`](/knowledge/concepts/api.md).

# Triggers

Runs start either from the [scheduler](/knowledge/concepts/scheduler.md) or a
manual `POST /api/pipeline/trigger`. Both use the same code path.
