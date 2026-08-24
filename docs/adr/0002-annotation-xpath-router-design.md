# 0002. Router design: SERP annotation & XPath testing

Status: accepted
Date: 2026-08-17

## Context

ADR 0001 decided the backend moves from Flask to FastAPI, with `backend/app/routers/` holding one module per route group, but left the actual route shapes for later. The old Flask app (`src/annotation/core/routes.py`) had 6 routes, casually designed over time:

- `GET /serp-id/<serp_id>` — fetch a SERP's HTML from the WARC store
- `GET /serp-ids` — list SERP ids, filtered by a server-side CLI-set session (`provider`/`year`/`language`)
- `GET /annotation` — serve the annotation UI's HTML file (now obsolete: the React frontend owns UI serving)
- `POST /save-annotation/<serp_id>` — save a human annotation
- `POST /test-xpath` — test an XPath expression against a `fb-testing`-marked element
- `GET /get-categories` — return the feature-block taxonomy

This decision covers only the **annotation** and **XPath-testing** workflows. The app's full scope also includes batch ground-truth validation (running a parser against many SERPs and comparing to stored ground truth) and interactive ground-truth editing — these are separate, more complex workflows deferred to their own future design passes, not folded in here.

## Decision

### REST-by-default, with explicit actions where there's no resource

Model genuine resources (things with identity and a stored representation) RESTfully. Don't force a computation into fake resource shape just for consistency — `xpath` testing takes `{html, xpath}` directly in its request body and doesn't reference any stored SERP, so it's a stateless action endpoint, not a resource route.

### Stateless: no server-side session

The old `/serp-ids` route filtered against a global session object set earlier via CLI arguments. The new design has no server-side session — filters (`provider`, `year`, `language`) are passed as query params on every request.

### Domain vocabulary: "category" → "feature type"

The taxonomy of SERP feature blocks was called "categories" throughout the old code (`serp_features_taxonomy.json`'s `categories` key, response field `"{provider} Feature Block Categories"`). Going forward the term is **feature type**. This ADR only decides the route name (`/features/type`); aligning the taxonomy file's key, response field names, and frontend labels to match is deferred implementation work, not done as part of this decision.

### Route table

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/serps/{serp_id}` | Fetch one SERP's HTML by id (`raw` query param for unmodified vs. cleaned HTML) |
| `GET` | `/serps` | List SERP ids matching `provider`/`year`/`language` query params |
| `GET` | `/serps/{serp_id}/annotation` | Fetch a SERP's saved annotation (404 if none exists) |
| `POST` | `/serps/{serp_id}/annotation` | Save (or overwrite) a SERP's annotation |
| `POST` | `/xpath` | Test an XPath expression against a marked HTML snippet |
| `GET` | `/features/type` | Get the feature-type taxonomy |

`annotation` is nested under `/serps/{serp_id}` because it's a genuine sub-resource of a specific SERP (one annotation per SERP, tied to that SERP's lifecycle). `xpath` and `features/type` are top-level: `xpath` because it isn't attached to any stored SERP, `features/type` because it's independent reference data with no relationship to any particular SERP.

**Open question, not yet resolved:** bare `/features` (no `/type` suffix) is reserved as a resource name but has no route registered under it yet — there's no defined meaning for `GET /features` today. It may eventually hold actual `FeatureBlock` instances (parser/annotation output), which would make `/features/type` read as "the taxonomy sub-resource of features," parallel to how `annotation` nests under a specific SERP. Confirm that reading, or that `/features` should stay undefined until a concrete use appears.

### Tentative: `/validation`

A placeholder for comparing parsed extraction results against ground truth (`validation.py`'s `compare_with_ground_truth`). Reserved as its own top-level path — not nested under `/xpath` — because it operates at a different scale (a batch of SERPs' worth of already-parsed results vs. `/xpath`'s single ad-hoc HTML/XPath pair) and isn't a child of the `xpath` action, just a peer that happens to reuse the same match-checking idea.

**Not yet decided:** whether the backend runs the parser itself given identifiers/config in the request, or receives already-parsed results from the caller. This also depends on a decision not yet made — whether ground-truth validation belongs in this HTTP API at all, versus staying a separate local script/tool (today's `gt_editor_server.py` is a standalone process launched by a script, with global in-memory state, not a client-callable route). Resolve before implementing this route.

## Consequences

- `GET /annotation` (UI-serving) has no replacement — the React frontend owns UI serving entirely, per ADR 0001.
- No `DELETE` route for annotations. The old code never had one and nothing in current requirements needs it; adding it now would be speculative (YAGNI). Revisit if a reset/clear workflow becomes a real need.
- Router file layout: `serps.py` holds both the SERP and annotation routes (annotation nests under `/serps/{serp_id}`, so it stays with the resource it belongs to); `xpath.py` and `features.py` are separate files for the two unnested resources.
- Aligning "category" → "feature type" outside of the route name (taxonomy file, response fields, frontend labels) is deferred implementation work.

## Out of scope (deferred to later decisions)

- **Batch ground-truth validation request shape**: whether `/validation` (reserved above as a placeholder) has the backend run the parser or accept pre-parsed results, and whether it belongs in this API at all vs. staying a separate script/tool.
- **Interactive ground-truth editing**: reviewing validation mismatches and correcting ground truth (`gt_editor_server.py`). No route reserved yet.

Both are substantial enough to warrant their own design pass once the annotation/XPath routes are implemented.
