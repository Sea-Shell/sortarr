---
type: Changelog
title: Sortarr Knowledge Bundle — Change Log
description: Chronological record of changes to the knowledge/ OKF bundle. Append one line per change; newest at top.
resource: https://github.com/Sea-Shell/sortarr
tags: [sortarr, log, okf, changelog]
timestamp: 2026-07-12T17:30:00Z
---

# Change Log

Append a one-line entry whenever you add, edit, or remove a concept doc.
Format: `- YYYY-MM-DD — <doc(s) touched> — <what changed and why>`

- 2026-06-24 — bundle created — initial OKF bundle: architecture, runtime-config, pipeline, filters, database, api, auth, scheduler, dev-workflow.
- 2026-06-24 — api.md, database.md — updated for sort_order column, reorder_pipelines function, ReorderRequest model, PUT /pipelines/reorder endpoint.
- 2026-07-08 — index.md, DESIGN.md — added DESIGN.md with responsive design system tokens, fluid typography, component inventory, and mobile-first layout rules. Direction B (Fluid Grid) confirmed by user.
- 2026-07-08 — pipeline.md — documented in-memory dedup by video_id in _collect_activities() to avoid redundant API calls.
- 2026-07-09 — api.md — updated subscriptions endpoint to DB-backed; added pipeline/runs/search route to route table; fixed route ordering note (literal paths before dynamic params).
- 2026-07-11 — api.md — added playlists route with YouTube API + DB fallback to route table.
- 2026-07-11 — api.md — enriched playlists fallback to also query distinct destination_playlist from pipelines table.
- 2026-07-11 — pipeline.md — added Subscription Sync section documenting DB persistence of subscriptions before Phase 1.
- 2026-07-11 — api.md — updated subscriptions endpoint to sync-then-serve pattern (YouTube API → DB fallback).
- 2026-07-12 — pipeline.md — documented restored per-subscription tracking narrowing in _compute_published_after (max() of reprocess_days ceiling and min_tracking_ts).
- 2026-07-12 — api.md — activity endpoint now falls back to activity_cache when YouTube API is unavailable.
- 2026-07-12 — architecture.md, index.md — v2 greenfield skeleton: deleted all v1 files, created new module layout with stubs. Added v1→v2 diff table and updated flow descriptions.
- 2026-07-12 — runtime-config.md — v2 Settings fields: removed v1 fields (pickle_file, credentials_file, log_file, compare_distance, playlist_sleep, etc.), added client_secret_path, public_url as env var. Added v1→v2 changelog section.
- 2026-07-12 — database.md — rewrote for v2: replaced v1 schema (channel, playlist, routing_rules, etc.) with v2 schema (14 tables, 6 indexes, V3_SCHEMA_SQL). Added init_db() description and repository layout.
- 2026-07-12 — database.md — added connection lifecycle (init_db/get_connection/close_db/connection_ctx), WAL mode, foreign keys, and pragma table.
- 2026-07-12 — filters.md — added duration filter to filter table, documented two-stage filter chain (cheap → duration), and described check_duration behavior (unknown durations pass through).
