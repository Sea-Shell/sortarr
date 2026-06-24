## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, invoke the `skill` tool with `skill: "graphify"` before doing anything else.

Rules:

- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Knowledge bundle (OKF) — MANDATORY maintenance

`knowledge/` is a curated OKF knowledge bundle (markdown + YAML frontmatter) that
agents and humans read to understand this project. **It is part of the source
tree, not optional documentation.** A change that makes a concept doc inaccurate
is an incomplete change.

**Rule: if you change source, you MUST update the matching concept doc in the
SAME change — before you consider the task done.** Treat a stale doc the same as
a failing test: a blocker, not a follow-up.

Source → doc mapping (touching the left column REQUIRES checking the right):

| If you change…                                      | You MUST review/update…                                     |
| --------------------------------------------------- | ----------------------------------------------------------- |
| `src/sortarr/config.py` (any `SORTARR_*` field)     | `knowledge/concepts/runtime-config.md`                      |
| `src/sortarr/core/pipeline.py` (phases, skip rules) | `knowledge/concepts/pipeline.md`                            |
| `src/sortarr/filters/**`                            | `knowledge/concepts/filters.md`                             |
| `src/sortarr/db/**` (schema, migrations, repos)     | `knowledge/concepts/database.md`                            |
| `src/sortarr/api/**` (routes, app, deps)            | `knowledge/concepts/api.md`                                 |
| `src/sortarr/core/auth.py`, `api/routes/auth.py`    | `knowledge/concepts/auth.md`                                |
| `src/sortarr/core/scheduler.py`, schedules          | `knowledge/concepts/scheduler.md`                           |
| module layout / new packages                        | `knowledge/concepts/architecture.md` + `knowledge/index.md` |
| build, deps, make targets, CI, Docker, K8s          | `knowledge/concepts/dev-workflow.md`                        |

Definition of done — ALL must hold before finishing a code change:

- [ ] Every doc in the mapping above whose source you touched has been updated (or you confirmed it is still accurate).
- [ ] You bumped the `timestamp:` frontmatter on every doc you edited (UTC ISO8601).
- [ ] Cross-links you added/changed still resolve to existing files under `knowledge/`.
- [ ] You appended a one-line entry to `knowledge/log.md` describing the change.

If a code change genuinely affects no concept doc, state that explicitly in your
summary (e.g. "no knowledge/ docs affected") so the omission is a decision, not
an oversight. Do not defer doc updates to a later task.
