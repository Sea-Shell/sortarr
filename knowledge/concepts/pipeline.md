---
type: Process
title: Sortarr Pipeline Runner
description: The 8-step Runner that orchestrates subscription fetching, activity collection, filtering, duration enrichment, and playlist insertion. Plus mock and cache preview modes for testing filter configurations without burning quota.
resource: https://github.com/Sea-Shell/sortarr/blob/main/src/sortarr/core/runner.py
tags: [sortarr, pipeline, runner, orchestration, core, preview]
timestamp: 2026-07-12T23:00:00Z
---

# Overview

`Runner` (`src/sortarr/core/runner.py`) executes the complete pipeline run flow.
It orchestrates subscription fetching, activity collection, filter execution,
batch duration enrichment, and playlist insertion. The runner enforces quota
limits, prevents concurrent runs, and maintains persistent activity cache.

# The 8-Step Run Flow

The `Runner.execute()` method executes these steps in order:

## Step 0: Startup Cleanup (Crash Recovery)

Clears any stale `run_active` flag from a previous crashed run. This ensures
the concurrency guard doesn't permanently block runs after an unclean shutdown.

## Step 1: Create Run Record

Creates a `pipeline_runs` record with `status="running"` and returns a `run_id`.
All subsequent operations reference this run ID for tracking and decisions.

## Step 2: Concurrency Guard

Checks if `app_config.run_active` is set. If yes, marks the run as `failed` with
`error_message="concurrent run blocked"` and returns immediately with a 409-equivalent
status. This prevents overlapping runs from corrupting state.

If no active run, sets `run_active="true"` to claim the lock.

## Step 3: Fetch Subscriptions

Calls `youtube.get_subscriptions()` with pagination to fetch all user subscriptions.
Upserts them into the `subscriptions` table. Tracks count in `run_summary.subscriptions_fetched`.

## Step 4: Fetch Activities Per Subscription

For each subscription (limited by `subscription_limit` if set):

1. Load tracking watermark from `subscription_tracking.last_fetched_at`
2. Compute `published_after`: use explicit override, or watermark, or `now - reprocess_days`
3. Call `youtube.get_activities()` with pagination
4. Filter client-side for `type="upload"` (API has no server-side filter)
5. Build `Activity` objects and collect into `all_activities`

Upserts all activities into the persistent `activity_cache` table. Tracks count
in `run_summary.activities_collected`.

## Step 5: Load Working Set

Loads all activities from `activity_cache` (not just newly fetched). This allows
filters to operate on historical data and supports cache-based preview.

## Step 6: Load Pipelines

Loads all enabled pipelines from the `pipelines` table. If `pipeline_id` is
provided, filters to that single pipeline. Converts `PipelineResponse` to
`PipelineConfig` for filter chain compatibility.

## Step 7: Run Cheap Filters Per Pipeline

For each pipeline:

1. Build filter context via `_build_filter_context()` (ignore lists, selectors, etc.)
2. Create a `FilterChain` instance
3. For each activity in working set:
   - Call `chain.run_cheap_filters(activity)`
   - If passes (returns `None`), add to survivors
   - If fails, record decision with `action="skipped"`, filter name, and reason

Cheap filters run **before** any duration enrichment. They include: subscription
scope, ignore lists (word/video/subscription), db_exists, title_similarity, and
selectors. See [filters](/knowledge/concepts/filters.md) for details.

## Step 8: Deduplicate Survivor Video IDs

Collects unique video IDs from survivors across **all** pipelines into a single
set. This ensures each video's duration is fetched only once, even if multiple
pipelines want to insert it.

## Step 9: Batch Enrich Durations

Uses the `Enricher` class to fetch durations via `youtube.get_videos_batch()`
in batches of 50 IDs. Returns a `duration_map: {video_id: seconds}`.

Updates `activity_cache.duration_seconds` for each enriched video. Tracks count
in `run_summary.videos_enriched`.

## Step 10: Quota Guard

Checks `get_quota_used()` against thresholds:

- **8,000 units (80%)**: Log warning
- **9,500 units (95%)**: Block inserts, mark run as `completed_quota_blocked`,
  record decisions for filtered videos, clear `run_active`, and return early.

This prevents burning the daily quota limit (10,000 units) on inserts when
already near the ceiling.

## Step 11: Run Duration Filters and Insert

For each pipeline:

1. For each survivor activity:
   - Create a new `FilterChain` with `duration_map` in context
   - Call `chain.run_duration_filter(activity, duration_map)`
   - If passes (returns `None`):
     - Call `youtube.insert_playlist_item()` (50 units)
     - Insert into `videos` table (audit trail)
     - Record decision with `action="inserted"`
     - Increment `run_summary.videos_inserted`
   - If fails:
     - Record decision with `action="skipped"`, filter name, and reason
     - Increment `run_summary.videos_skipped`

Duration filters include: `min_duration`, `max_duration`.

## Step 12: Update Watermarks

For each subscription, updates `subscription_tracking.last_fetched_at` to the
current timestamp. This advances the watermark for the next run.

## Step 13: Record Run Summary

Updates the `pipeline_runs` record with:

- `status="completed"`
- `finished_at=<timestamp>`
- All summary counts (subscriptions, activities, videos enriched/inserted/skipped)
- `quota_used=<current quota>`

Batch-inserts all decisions into `run_decisions` table.

## Step 14: Clear Run Lock

Sets `app_config.run_active=""` to release the concurrency lock.

## Step 15: Prune Activity Cache

Calls `activities.prune_old_entries(retention_days=30)` to delete cache entries
older than 30 days. This keeps the cache size manageable.

# Error Handling

If any exception occurs during the run:

1. Log the exception with full stack trace
2. Update the run record with `status="failed"` and `error_message`
3. Clear `run_active` flag (critical for recovery)
4. Re-raise the exception

This ensures the concurrency lock is never left stale after a failure.

# Quota Budget

Typical run (200 subscriptions, 4 pipelines, 12 inserts):

- `subscriptions.list`: 4 calls = 4 units
- `activities.list`: 200 calls = 200 units
- `videos.list`: 4 batches = 4 units
- `playlistItems.insert`: 12 calls = 600 units
- **Total**: ~808 units per run

With 4 runs/day (6-hour schedule), typical daily usage is ~3,200 units (32% of limit).

# Triggers

Runs start either from the [scheduler](/knowledge/concepts/scheduler.md) or a
manual `POST /api/run` endpoint. Both call `Runner.execute(mode="run")`.

# Concurrency

Only one run can execute at a time. The `run_active` flag in `app_config` acts
as a mutex. Concurrent run attempts receive a `failed` status immediately.

# Preview Modes

sortarr v2 provides two preview modes that let users test filter configurations
**without making YouTube API calls or burning quota**. Both return `quota_cost: 0`.

## Mock Preview

**Purpose**: Test filter logic before any real data exists.

**How it works**:

1. Generates deterministic synthetic test activities (one per filter rule + baseline)
2. Each mock targets a specific filter to verify it triggers correctly
3. Runs the full filter chain (cheap + duration) on each mock
4. Returns per-pipeline breakdown with filter results

**Mock types generated**:

- **Baseline**: "passes all filters" — verifies the happy path
- **Word filter**: One mock per word in word-type ignore lists (title contains that word)
- **Video ignore**: One mock per video ID in video-type ignore lists
- **Subscription ignore**: One mock per subscription ID in subscription-type ignore lists
- **Duration boundaries**: Mocks below `duration_min_seconds` and above `duration_max_seconds`
- **Selectors**: Mocks that match and don't match configured selectors (if any)

**Acceptance criteria verified**:

- The "passes all" mock actually passes all configured filters (per critic finding)
- Each filter-specific mock is caught by its target filter
- Zero YouTube API calls, zero quota cost

**Use case**: Configure a new pipeline, run mock preview, verify each filter
triggers as expected before enabling the pipeline.

## Cache Preview

**Purpose**: Test filter logic on real historical data without API calls.

**How it works**:

1. Reads from persistent `activity_cache` table (populated by prior runs)
2. Applies full filter chain (cheap + duration) to cached activities
3. Uses cached `duration_seconds` values (no `videos.list` calls)
4. Returns per-pipeline breakdown with counts at each stage

**Response includes**:

- `total_activities`: All activities in cache
- `activities_after_cheap`: Survivors after cheap filters
- `activities_after_duration`: Survivors after duration filters
- `duration_unknown_count`: Activities with `duration_seconds = NULL` (counted, not blocked per critic finding)
- `quota_cost: 0`

**Acceptance criteria verified**:

- Duration-unknown activities are counted but NOT blocked
- Returns empty results when cache is empty (no error)
- Zero YouTube API calls, zero quota cost

**Use case**: Adjust filter thresholds (e.g., change `duration_min_seconds`),
run cache preview, see how many cached videos would pass with the new settings.

## Implementation

Both preview modes live in `src/sortarr/core/preview.py`, separated from run
logic per design gate requirement. They reuse the same `FilterChain` and filter
functions as the live runner, ensuring preview results match real run behavior.

**API endpoints** (Phase 5):

- `POST /api/preview/mock` — mock preview for one or all pipelines
- `POST /api/preview/cache` — cache preview for one or all pipelines

Both accept `{"pipeline_id": "uuid" | null}` and return a list of preview responses.

