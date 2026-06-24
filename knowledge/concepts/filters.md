---
type: Component
title: Sortarr Filters
description: The four filter functions that decide whether a discovered video is routed or skipped — ignore list, word, selector, and fuzzy title similarity.
resource: https://github.com/Sea-Shell/sortarr/tree/main/src/sortarr/filters
tags: [sortarr, filters, deduplication, routing]
timestamp: 2026-06-24T10:00:00Z
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
