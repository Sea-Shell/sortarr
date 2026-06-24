---
type: Runbook
title: Sortarr Development Workflow
description: How to install, run, test, lint, type-check, containerize, and deploy sortarr — the commands you reach for every session.
resource: https://github.com/Sea-Shell/sortarr/blob/main/README.md
tags: [sortarr, dev, build, test, docker, k8s]
timestamp: 2026-06-24T10:00:00Z
---

# Stack

- Python **3.13**, packaged with **uv** (`pyproject.toml`, hatchling build).
- Runtime: FastAPI + uvicorn[standard], APScheduler, pydantic-settings,
  google-api-python-client / google-auth(-oauthlib), prometheus-client, httpx,
  fuzzywuzzy + levenshtein.
- Version `2.0.0`. Entry point script: `sortarr = sortarr.__main__:main`.

# Run locally

```sh
uv sync --dev
uv run python -m sortarr      # serves http://localhost:8080
```

# Make targets

| Command       | Does                                        |
| ------------- | ------------------------------------------- |
| `make sync`   | install dependencies                        |
| `make test`   | run tests (`pytest`, `asyncio_mode = auto`) |
| `make lint`   | `ruff check`                                |
| `make format` | `ruff format`                               |
| `make check`  | lint + format check                         |
| `make docker` | build the container image                   |

# Lint / format / types

- `ruff` for lint + format; runs on commit via **pre-commit**
  (`uv tool install pre-commit && pre-commit install`).
- Optional type checking: `uv run mypy src/sortarr/`.

# Tests

`pytest` with `pytest-asyncio` (auto mode). Integration tests use a real
in-process app + DB `Connection` (see graphify "Integration Tests" community);
no external services required.

# Docker

```sh
make docker
docker run -p 8080:8080 -v /path/to/data:/data sortarr
```

# Kubernetes

Manifests in `k8s/` — `kubectl apply -f k8s/`. The old `cronjob.yaml` is
superseded by the internal [scheduler](/knowledge/concepts/scheduler.md).

# Knowledge graph

A graphify graph exists at `graphify-out/` (`graph.json`, `GRAPH_REPORT.md`).
Prefer `graphify query "<question>"` for codebase questions; run
`graphify update .` after changing code. This OKF bundle complements it with
hand-curated, navigable summaries.
