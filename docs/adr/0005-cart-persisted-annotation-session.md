# 0005. Cart: a persisted annotation working session

Status: accepted
Date: 2026-08-21

## Context

ADR 0002 designed the landing-page filtering workflow as fully stateless: `GET /serps` was reserved to "list SERP ids matching provider/year/language query params," with filters passed fresh on every request and nothing remembered server-side.

Building the actual landing page surfaced a real need that decision didn't anticipate: knowing, after the fact, who annotated which SERPs, under what criteria, and when — "who did what annotation for which SERP IDs" — for later review across multiple people/sittings. A stateless filter can't answer that; nothing persists the fact that a particular provider/year/language selection was ever made, or by whom.

Separately, this workflow's SERP-matching source is not AQL's live Elasticsearch cluster (ADR 0003's direct-ES-access decision still stands for other purposes) but a JSONL manifest file — a hand-curated, pre-selected list of "SERPs worth annotating" (`id`/`provider`/`language`/`year`/...), produced by a separate offline script the user maintains outside this repo, refreshed independently. This is not a reintroduction of the old Flask app's `session.py` ids-cache (which ADR 0003 moved away from as a bulk-ES-access concern) — it's a different, smaller-scoped input: a deliberately curated worklist, not a full index mirror.

## Decision

### A new persisted resource: `Cart`

`Cart` (`backend/persistence.py`) records that a working session was opened: `id` (UUID, PK), `provider`, `year`, `language`, `created_by` (free text — no login system exists yet), `created_at`. This reverses ADR 0002's "no server-side session" rule specifically for this workflow — the trade-off (a small amount of state, in exchange for an audit trail across sittings) is worth it here, since nothing else provides that traceability.

`Cart` deliberately does **not** persist the resolved list of matching SERP ids. That list is computed fresh at creation time (see below) and handed to the frontend in the response; it only needs to survive in the browser for the duration of that sitting, since the frontend pages through it one SERP at a time. Persisting it would only matter if *resuming* an unfinished cart across sessions became a real requirement — it isn't one today. (A `CartSerp` join table for exactly this was designed and then cut for this reason; see `CONTEXT.md`'s `Cart` entry.)

`Annotation` (unchanged otherwise, per ADR 0004) gets one new column: `cart_id` (FK → `Cart.id`) — so a completed annotation always traces back to the session it was done under.

### New route: `POST /carts`

Supersedes ADR 0002's reserved (and never-implemented) `GET /serps` list route for this specific purpose. Creating a cart is no longer a pure read — it's a resource creation with a side effect (a persisted `Cart` row) — so `POST` on a new `/carts` resource fits better than forcing it into `/serps`. `GET /serps` reverts to reserved-but-undefined, alongside `/features`'s already-noted open status in ADR 0002.

Request: `{provider, year, language, created_by, batch_size}` (`batch_size` defaults to 25 — without a cap, broad criteria could hand back thousands of ids nobody will get through in one sitting).

Behavior:
1. `backend/manifest.py` (new module) reads the JSONL manifest and filters by `provider`/`year`/`language`.
2. Matching ids that already have an `Annotation` row are excluded (a global check against `Annotation`, not scoped to any one cart — a SERP finished under an earlier cart must never be re-offered).
3. Remaining ids are capped to `batch_size`.
4. If the result is empty, no `Cart` row is persisted — nothing worth recording happened. Response is `{id: null, serp_ids: [], total: 0}`.
5. Otherwise, one `Cart` row is persisted, and the response is `{id, serp_ids, total}`.

`manifest.py` is a separate module from both `orm.py` (scoped to AQL's live ES mirror, per ADR 0003) and `persistence.py` (scoped to this app's own annotation/parser storage, per ADR 0004) — it reads a third, distinct data source: the externally-produced manifest snapshot.

### Consequential change: `save_annotation`

`save_annotation()` (`backend/persistence.py`) gains a new `cart_id` parameter — a property of the annotation event itself, not of any individual feature — threaded through when the (not-yet-built) annotation workspace calls it.

## Consequences

- `config.py` gains a new field for the manifest file's path (same `.env`-driven, `cached_property` style as `PersistenceConfig`'s existing fields).
- No new dependency: JSONL parsing uses the standard library `json` module, one line at a time.
- Closing the browser tab mid-session loses track of which SERPs in that cart's batch remain unannotated — the server has no record of the offered set, only of completed `Annotation`s. Acceptable today; revisit (e.g., a join table recording the offered batch) if resuming an unfinished cart becomes a real need.
- `GET /serps` (ADR 0002) is no longer this workflow's route; it stays reserved, undefined, alongside `/features`.

## Out of scope (deferred to later decisions)

- **Resuming an unfinished cart** — would require persisting the offered batch (a `CartSerp`-shaped table) and a route to fetch it back; no concrete need yet.
- **The annotation workspace itself** — fetching one SERP's HTML at a time from S3 and saving its `Annotation`/`AnnotatedFeature`s, now carrying `cart_id` — a separate task, using the `serp_ids` this route already hands back.
- **Manifest file format/schema specifics** — owned by the external script that produces it; this decision only concerns how `manifest.py` reads whatever fields it needs (`id`, `provider`, `language`, `year`), tolerant of any extra fields present.
