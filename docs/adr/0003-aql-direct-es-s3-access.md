# 0003. AQL live integration: direct Elasticsearch + S3 access

Status: accepted
Date: 2026-08-17

## Context

ADR 0001 deferred one question explicitly: "whether the backend calls AQL's FastAPI over HTTP or continues importing `archive_query_log` directly, and how ES/S3 credentials are configured." At the time, `archive_query_log` wasn't installed and there was no manifest for it.

The workload driving this decision: the annotation app needs to run a custom xpath-based parser over many SERPs — not fetch one SERP at a time for a human to look at, but walk a large slice of AQL's index. That volume shapes the answer.

An earlier draft of this integration (worked out in a separate conversation against the AQL project itself) proposed routing metadata reads through AQL's FastAPI backend, specifically to avoid holding ES credentials in this repo. That reasoning no longer applies: ES and S3 credentials for this project are already in hand (gated by whoever manages Webis's infrastructure), so avoiding a small amount of config duplication is no longer a cost worth optimizing for. AQL's own bulk tooling (`aql serps parse ...`, `archive_query_log/export/jsonl.py`) goes straight to Elasticsearch for the same reason: the rate-limited API (15–120 req/min per route) is for light, interactive access; direct ES is for bulk processing.

## Decision

| Need | Source | Notes |
|------|--------|-------|
| SERP metadata, at volume | AQL's Elasticsearch cluster, direct | No rate limit; own credentials |
| Archived page HTML | AQL's S3 WARC store, direct, via `warc-s3` | Own credentials |
| `archive-query-log` Python package | *(not used)* | Pre-1.0 (`0.3.x`), no stability guarantees, no `[project.optional-dependencies]` split — installing it pulls `ray[data]`, `resiliparse`, `pandas`, `fastapi`, `fastmcp`, `python-whois`, ~30 packages total, to get two files' worth of code |
| AQL FastAPI backend | *(not the parsing path)* | Fine for one-off interactive lookups during development; its per-route rate limits aren't built for bulk parsing |

Two direct dependencies on AQL's infrastructure (its ES cluster, its S3 bucket); zero dependency on its Python package or its rate-limited HTTP API.

### Config shape

`backend/config.py` holds `EsConfig` and `S3Config` (both `pydantic-settings`, `.env`-driven), combined into one `Config`. Same shape as AQL's own `config.py`, trimmed to read-only fields — no bulk-write helpers (`streaming_bulk`, etc.), since this app only reads. `.env` variable names mirror AQL's own naming (`ELASTICSEARCH_*` prefix) so credentials can be copied straight out of AQL's local `.env` rather than renamed.

### Data model

`backend/aql/models.py` (originally `backend/orm.py`) holds a copied slice of `archive_query_log/orm.py` — `UuidBaseDocument`, the `Inner*` sub-documents, and `Serp` itself, built on `elasticsearch-pydantic`'s `BaseDocument`/`BaseInnerDocument` (gives `.search()` / `.get()` / `.mget()`). `OrganicResult`/`Feature` are left out for now: the current xpath parser works on top-level SERP feature blocks, not organic result blocks. Add them if that changes.

### Access pattern

Bulk metadata reads use `elasticsearch-dsl`'s `Search.scan()` (scroll-based, paginates past the default 10k window, no rate limit) rather than manual `from_`/`size` paging. For each `Serp` with a non-null `warc_location`, HTML comes from `warc_s3_store.read(WarcS3Location(...))`, and the parser runs on the resulting `html_bytes`.

### Dependencies

```
elasticsearch~=7.17
elasticsearch-dsl~=7.4
elasticsearch-pydantic~=1.1
warc-s3~=1.0
pydantic-settings~=2.12
python-dotenv~=1.1
```

`elasticsearch` is pinned to the `7.17` line deliberately — its wire protocol isn't compatible with `elasticsearch-py` 8.x, and this has to match whatever AQL's actual cluster runs.

## Consequences

- `.env` (real credentials) must never be committed; add to `.gitignore`.
- `warc_location` is nullable — not every SERP has been through AQL's WARC-caching pipeline stage. The parser must skip or flag those rather than treat a missing location as an error.
- The copied `aql/models.py` subset can drift from AQL's real index mappings over time (new fields, renames). Since reads no longer go through the API, nothing surfaces a mismatch except a parse-time validation error — worth a periodic diff against upstream `orm.py`.
- The AQL FastAPI backend remains available for quick manual single-SERP lookups during development; this decision only removes it from the bulk-parsing path.

## Out of scope (deferred to later decisions)

- **Wiring this into `backend/app/routers/serps.py`**: the route stubs from ADR 0002 still need to be implemented against `config.es.client` / `config.s3.warc_s3_store`.
- **`backend/namespaces.py`**: currently an empty stub; its purpose relative to this integration is unresolved.
- **`OrganicResult`/`Feature` ORM docs**: add if the xpath parser grows to extract organic result blocks, not just top-level features.
