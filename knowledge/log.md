---
type: Changelog
title: Sortarr Knowledge Bundle — Change Log
description: Chronological record of changes to the knowledge/ OKF bundle. Append one line per change; newest at top.
resource: https://github.com/Sea-Shell/sortarr
tags: [sortarr, log, okf, changelog]
timestamp: 2026-06-24T10:00:00Z
---

# Change Log

Append a one-line entry whenever you add, edit, or remove a concept doc.
Format: `- YYYY-MM-DD — <doc(s) touched> — <what changed and why>`

- 2026-06-24 — bundle created — initial OKF bundle: architecture, runtime-config, pipeline, filters, database, api, auth, scheduler, dev-workflow.
- 2026-06-24 — api.md, database.md — updated for sort_order column, reorder_pipelines function, ReorderRequest model, PUT /pipelines/reorder endpoint.
- 2026-07-08 — index.md, DESIGN.md — added DESIGN.md with responsive design system tokens, fluid typography, component inventory, and mobile-first layout rules. Direction B (Fluid Grid) confirmed by user.
- 2026-07-08 — pipeline.md — documented in-memory dedup by video_id in _collect_activities() to avoid redundant API calls.
- 2026-07-09 — api.md — updated subscriptions endpoint to DB-backed; added pipeline/runs/search route to route table; fixed route ordering note (literal paths before dynamic params).
