---
type: Process
title: Sortarr Pipeline Orchestrator
description: The two-phase PipelineOrchestrator that collects subscription activity then routes videos into playlists per pipeline, with skip rules.
resource: https://github.com/Sea-Shell/sortarr/blob/main/src/sortarr/core/pipeline.py
tags: [sortarr, pipeline, routing, core]
timestamp: 2026-07-12T00:00:00Z
---

# Overview

`PipelineOrchestrator` (`src/sortarr/core/pipeline.py`) executes a full routing
run. It is constructed with `Settings`, a `YouTubeAPIClient`, a DB `Connection`,
the user's `Channel`/`Playlist`, the list of `PipelineConfig`s, resolved ignore
lists, a default playlist, and an optional `dry_run` flag and `on_progress`
callback. Entry point is `_run()`, returning a `PipelineSummary`.

# Subscription Sync

After fetching subscriptions from the YouTube API and before Phase 1, the
orchestrator persists every subscription to the `subscription` DB table via
`v.insert_subscription()` (which uses `INSERT OR REPLACE`). This keeps the
DB-backed subscriptions endpoint in sync with the user's actual YouTube
subscriptions on every pipeline run.

# Phase 1 — Data Collection

`_collect_activities(subscriptions)` fetches activity for **every** subscription
once via `youtube.get_subscription_activity(...)` and caches each `Activity` into
the [`videos` cache table](/knowledge/concepts/database.md). Returns
`{sub_id: [Activity]}`.

The lookback (`published_after`) is computed by `_compute_published_after`:

1. use `settings.published_after` if set, else
2. compute a **maximum window** (`now - reprocess_days`, or `now - 52 weeks`).
3. narrow it with per-subscription tracking: `max(max_window, min_tracking_ts)` —
   the **later** (more recent) of the two wins, fetching only unseen activity.

`get_min_tracking_for_subscription()` returns the earliest `last_processed`
across **all** pipelines for that subscription. Using `max()` on ISO8601 strings
ensures no pipeline gets a window wider than `reprocess_days` (the ceiling),
while any subscription with existing tracking gets a tighter fetch window.

The in-memory list (`activity_objects`) is **deduplicated by `video_id`** before
being returned — if the YouTube API returns the same video as both an `upload`
and a `playlistItem` entry, only the first occurrence (earliest `published_at`
since results are sorted) is kept. This avoids redundant `get_video_duration()`
API calls and inflated decision counters in Phase 2.

The DB cache (`cache_activity()`) still writes **every** entry unconditionally;
it relies on `INSERT OR REPLACE` for its own dedup.

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
