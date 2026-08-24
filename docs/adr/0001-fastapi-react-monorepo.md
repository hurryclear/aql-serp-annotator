# 0001. FastAPI backend, React frontend, monorepo layout

Status: accepted
Date: 2026-08-03

## Context

sis project. It ran as a single Flask process: `src/annotation/core` served both JSON-ish API routes (fetch a SERP's HTML, save an annotation, test an XPath) and the annotation UI itself (`src/annotation/frontend/annotation.html`, a single ~1567-line file with vanilla JS). `src/parser` and `src/validation` hold framework-agnostic logic (HTML normalization, XPath testing, ground-truth comparison) with no Flask dependency.

The goal is to turn this into a standalone web application: containerized (Docker), with CI/CD, eventually talking to AQL's Elasticsearch/S3-backed data over AQL's own FastAPI (`archive_query_log.api`) instead of importing `archive_query_log` directly as a Python library. This decision covers the first thing everything else depends on: what stack and repo structure to build toward, so Docker and CI/CD have something concrete to target. AQL live integration, full UI feature parity, and an actual deployment target are separate, later decisions — see "Out of scope" below.

AQL itself (`webis-de/archive-query-log`) was used as a reference: it's a monorepo with a FastAPI backend (`archive_query_log/api/`, routers for `/serps`, `/providers`, `/archives`) and a separate Angular frontend (`browser/`), each with its own Dockerfile, orchestrated via one GitHub Actions workflow with parallel jobs for backend lint/typecheck/test and frontend build.

## Decision

### Stack: FastAPI backend + React frontend

- **Backend: FastAPI**, replacing Flask. Its job becomes purely serving data (JSON) — no more serving `annotation.html` directly. This matches AQL's own backend, and the migration cost is small: the app currently has 6 routes total.
- **Frontend: React**, not Angular. Angular would match AQL's `browser` exactly and could theoretically reuse its components, but React has more learning material and is a smaller step up from the current vanilla-JS file, which matters given frontend frameworks and Docker/CI are both new territory here. Angular remains an option to revisit if a concrete reuse case from AQL's `browser` shows up later.
- **Business logic is framework-agnostic already.** `src/parser` (models, HTML normalization) and `src/validation` (XPath testing, ground-truth comparison) don't import Flask — they move into the new backend largely unchanged. Only `src/annotation/core` (Flask routes/session/server glue) gets rewritten as FastAPI routers.

### Repo layout: one repo, two top-level folders

Mirrors AQL's monorepo pattern:

```
/
├── backend/              # FastAPI app
│   ├── pyproject.toml    # first dependency manifest this repo will have
│   ├── Dockerfile
│   └── app/
│       ├── main.py       # FastAPI app instance, router registration
│       ├── routers/      # one module per route group (serps, annotations, categories)
│       ├── parser/       # moved from src/parser, unchanged
│       ├── validation/   # moved from src/validation, unchanged
│       └── utils/        # moved from src/utils, unchanged
├── frontend/             # React app
│   ├── package.json
│   ├── Dockerfile        # multi-stage: node build -> nginx runtime, same pattern as AQL's browser/Dockerfile
│   └── src/
├── docker-compose.yml    # runs backend + frontend together for local dev
└── .github/workflows/    # CI: lint/test backend, lint/build frontend, build both images
```

`src/` (the current Flask-based layout) is retired once the port is complete; it is not kept alongside `backend/` as a second copy.

## Consequences

- Backend routes get rewritten (Flask → FastAPI routers, `jsonify` → Pydantic models); FastAPI's request validation replaces manual `try/except` + `jsonify({"error": ...})` blocks.
- `src/parser` and `src/validation` move with minimal changes, including their existing `pytest` suite, since neither imports Flask.
- The annotation UI gets rebuilt from scratch as React components rather than ported line-by-line from `annotation.html` — full feature parity (category picker, XPath tester, GT editor UI) is separate follow-up work, not part of this decision.
- `gt_editor_server.py`'s server-rendered HTML pages (`/gt/<serp_id>`, `/ext/<serp_id>`) don't fit the API-only backend model as-is; whether they become a React view or stay a separate local dev tool is unresolved.
- Docker/CI/CD work (Dockerfiles, `docker-compose.yml`, GitHub Actions) now has a concrete structure to target.

## Out of scope (deferred to later decisions)

- **AQL live integration**: whether the backend calls AQL's FastAPI over HTTP or continues importing `archive_query_log` directly, and how ES/S3 credentials are configured. `archive_query_log` isn't installed in this environment and there's no manifest for it yet.
- **Full frontend feature migration**: porting the entire annotation workspace into React components.
- **Deployment target**: where the built Docker images actually run is undecided.
