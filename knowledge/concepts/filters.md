---
type: Component
title: Sortarr Filters
description: The filter functions that decide whether a discovered video is routed or skipped — ignore list, word, selector, title similarity, and duration.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr/filters
tags: [sortarr, filters, deduplication, routing]
timestamp: 2026-07-12T17:30:00Z
---

# Filter functions

All live in `src/sortarr/filters/` and return a `FilterResult`
(`passed: bool`, plus reason / `skipped_by` / match metadata). Used by the
[pipeline](/knowledge/concepts/pipeline.md) during Phase 2.

| Filter               | File                  | Purpose                                                                    |
| -------------------- | --------------------- | -------------------------------------------------------------------------- |
| `ignore_list_filter` | `ignore_list.py`      | Reject if video id is in an ignore list                                    |
| `word_filter`        | `word_filter.py`      | Reject if the title contains an ignored word                               |
| `selector_filter`    | `selector_filter.py`  | Match against pipeline selectors (field/operator/pattern, combined AND/OR) |
| `title_similarity`   | `title_similarity.py` | Reject near-duplicate titles already in the DB                             |
| `check_duration`     | `duration_filter.py`  | Reject if video duration falls outside pipeline min/max boundaries         |

# Filter stages

Filters run in two stages:

1. **Cheap** (no API calls): `word_filter`, `ignore_list`, `db_exists`, `selector_filter`, `title_similarity` — run against cached activity data.
2. **Duration** (needs enrichment): `check_duration` — runs after the batch enricher populates the shared `duration_map`.

The runner enforces this ordering (cheap → duration → insert) per invariant I8.

# Duration filter

`check_duration(activity, pipeline, context)`:

- Reads `pipeline.duration_min_seconds` and `pipeline.duration_max_seconds`.
- If both are `None`, the filter is a no-op (returns `None` = passed).
- Looks up `activity["video_id"]` (fallback: `activity["id"]`) in `context["duration_map"]` — a `dict[str, int]` mapping video_id to seconds.
- **Unknown duration** (`None`, `0`, or missing from map): logs a warning and passes through. Never blocks.
- Returns `FilterResult(passed=False, filter_stage=DURATION)` with a human-readable reason when duration is outside bounds.

# Title similarity (de-duplication)

This is the non-obvious one. `title_similarity(new_title, existing_titles, threshold)`:

1. `_normalize()` lowercases and collapses non-`[a-zA-Z0-9-_]` runs to spaces.
2. `_fuzz_ratio()` computes a **Levenshtein-based** similarity percentage
   (0–100) between the normalized new title and each existing title.
3. If `ratio > threshold`, the video is rejected as a duplicate, citing the
   matched `video_id` and percentage.

The threshold is `SORTARR_COMPARE_DISTANCE` (default **80**) — see
[runtime config](/knowledge/concepts/runtime-config.md). The implementation is a
hand-rolled edit-distance loop; `fuzzywuzzy` / `levenshtein` are also project
dependencies.

> Search note: this is what answers "how does sortarr detect duplicate videos?"
> — the code never uses the word "duplicate", it talks about _title similarity_.

# Ignore lists

Ignore lists are DB-backed (managed in the web UI, not `.ignore` files) and typed
as `video`, `word`, or `subscription`. A pipeline references list ids; the
orchestrator resolves them into concrete value lists before filtering. See the
[`ignore_lists` repository](/knowledge/concepts/database.md).
