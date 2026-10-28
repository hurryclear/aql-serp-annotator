# 0004. Local annotation & parser-rule storage: SQLite + file snapshots

Status: accepted
Date: 2026-08-18

## Context

ADR 0002 defined `GET`/`POST /serps/{serp_id}/annotation` but left open where annotation data actually lives. ADR 0003 settled that AQL's Elasticsearch is read-only — annotations can't be written back into AQL's index, so this app needs storage of its own.

Three distinct things need to persist:

1. **Structured annotation data** — the human's work: which feature blocks were found on a SERP, and their type/xpath/content. This is a scoped-down version of the domain shape expressed by the `FeatureBlock`/`Answer` dataclasses in `src/parser/models.py` — ground truth here deliberately excludes answer text/source link (see `AnnotatedFeature` below).
2. **The annotated SERP's HTML** — kept as a stable ground-truth snapshot. The original HTML is available live via AQL's S3 WARC store (ADR 0003), but ground truth needs to survive independently of that store's own retention/consistency, so it's saved rather than reconstructed on demand.
3. **Reusable xpath parser rules** — while developing a parser against annotated ground truth, the derived rule (which xpath locates a feature block, its text, its source link, for a given provider/feature type) needs saving too, and running that rule locally against SERPs (not necessarily annotated ones) also produces feature instances that need saving. Multiple candidate rules can exist for the same provider/feature type at once, for comparison during parser design.

This app's own scale is "thousands, for annotation and parser design/testing" — not the millions-of-SERPs automated mining an earlier related project (a thesis codebase living outside this repo, at `.../thesis-jiang/src`) was built for. That thesis code's id-generation scheme (content-hashed, namespaced UUIDs) is the direct ancestor of the scheme below, adapted down to this project's smaller, human-in-the-loop scale.

### Two origins of a "feature," not one

A feature block instance can come from two different sources, and a single `Feature` table with optional/nullable columns for both turned out to be the wrong shape: whichever origin a given row came from, the *other* origin's columns would sit there unset. That's the classic sign of a supertype with two subtypes, not one entity with optional extra fields — so the design splits into three tables: a shared `Feature`, plus `AnnotatedFeature` (human ground truth) and `ParsedFeature` (automated extraction output) each holding only what's specific to their origin.

## Decision

### Storage mechanisms

- **Structured data → SQLite via SQLAlchemy.**
- **SERP HTML → a file on disk per SERP** (e.g. `data/annotated_serps/{serp_id}.html`), not a database blob column — keeps the database small and the HTML directly greppable/diffable.
- Both are accessed only through a repository package, `backend/persistence/` (`models.py` tables, `database.py` session factory, and `carts.py`/`annotations.py`/`serp_store.py` operations), exposing `save_annotation`, `get_annotation`, `get_feature`, `save_serp_html`, `get_serp_html`. Routes call this package; they never open a SQLAlchemy session or a file directly.
- `persistence/` holds only storage mechanics: the SQLAlchemy models, `SessionLocal`, and the repository functions. It deliberately does **not** define the DTOs those functions accept/return, or any custom exceptions — those live in `backend/schemas.py` and `backend/exceptions.py` respectively, so that "what data looks like to the rest of the app" stays separate from "how it's stored."
- Storage location is configurable via `.env`, following the existing `EsConfig`/`S3Config` pattern in `backend/config.py`.
- The snapshot directory (and the SQLite file) are gitignored — this is generated/derived data, not source.

### Tables

- **`Annotation`** (renamed from `AnnotatedSerp`, for consistency with `save_annotation`/`get_annotation`) — `serp_id` (UUID, primary key — same UUID as AQL's `Serp.id`, one annotation per SERP per ADR 0002), `created_at`, `updated_at`.
- **`Feature`** (shared base, no origin-specific fields) — `id` (UUID, primary key, deterministic — see below), `type`, `content` (the raw markup of the matched DOM element, not an extracted answer). No `query` field — a feature's query is only ever needed alongside its SERP context, and duplicating it here added no value over looking it up via the SERP.
- **`AnnotatedFeature`** — `feature_id` (UUID, both primary key *and* foreign key → `Feature.id`, a strict one-to-one link), `annotated_serp_id` (FK → `Annotation.serp_id`), `xpath` (where the human found this instance in the DOM). Deliberately holds **no answer text/source link** — ground truth is scoped to "this type of feature exists at this location" for now, not the extracted answer itself. Kept simple on purpose; revisit if a future `/validation` pass needs answer-level ground truth to compare against. No history is kept across re-annotation: `save_annotation` deletes a SERP's prior `AnnotatedFeature` rows outright and inserts a fresh set on `overwrite=True` (an earlier `is_current`-flag soft-delete design was tried and reverted — it collided with `Feature.id`'s content-addressing, since a `feature_id` is also this table's primary key and can't be referenced by more than one row, ever, even a "flagged old" one).
- **`ParsedFeature`** — `feature_id` (same one-to-one pattern as above), `serp_id` (plain UUID column, **not** a foreign key — the SERP a parser was tested against, which may not have any local `Annotation` row), `feature_parser` (FK → `FeatureParser.id`, which parser rule produced this instance; that rule's own `xpath` covers "where," so no separate xpath is stored per instance), `text`, `source_link` (both nullable — a feature has at most one answer, so this is inlined directly rather than a separate table; no `Answer` class exists).
- **`FeatureParser`** — `id` (UUID, primary key, deterministic — see below), `provider` (UUID, matching AQL's `Serp.provider.id`), `feature_type`, `xpath` (locates the feature block), `text_xpath`, `source_link_xpath`. **Not** unique per `(provider, feature_type)` — multiple candidate parsers can coexist for comparison while a rule is being designed. (Named `feature_type`, not `type`, to stay unambiguous when read outside the table's context — a deliberate stylistic choice over matching `Feature.type`'s exact name.)

### Deterministic ids

`backend/namespaces.py` holds a namespace hierarchy:

```python
NAMESPACE_AQL_SERP_ANNOTATOR = uuid5(NAMESPACE_URL, "aql-serp-annotator")
NAMESPACE_FEATURE = uuid5(NAMESPACE_AQL_SERP_ANNOTATOR, "feature")
NAMESPACE_FEATURE_PARSER = uuid5(NAMESPACE_AQL_SERP_ANNOTATOR, "feature_parser")
```

- `Feature.id = uuid5(NAMESPACE_FEATURE, f"{serp_id}:{type}:{sha256(content)}")` — `serp_id` here is whichever SERP this instance is associated with (`AnnotatedFeature.annotated_serp_id` or `ParsedFeature.serp_id`), known by the caller at construction time in `persistence/`, not stored on `Feature` itself. Re-saving identical content for the same SERP/type reproduces the same id; different content (or a second block of the same type) gets a distinct one.
- `FeatureParser.id = uuid5(NAMESPACE_FEATURE_PARSER, f"{provider}:{feature_type}:{xpath}:{text_xpath}:{source_link_xpath}")` — the id is derived from the rule's actual content, so two different xpath definitions for the same `(provider, feature_type)` naturally get different ids and coexist as separate rows.
- Content is hashed with `hashlib.sha256`, not Python's built-in `hash()` — the builtin is randomized per process (`PYTHONHASHSEED`) and would make these ids non-reproducible across restarts.

### Repository function behavior

- `save_annotation(serp_id, features: list[AnnotatedFeatureInput], overwrite: bool = False)` — since `Annotation.serp_id` is a primary key (one annotation per SERP, per ADR 0002), calling this a second time for an already-annotated SERP raises `AnnotationExistsError` unless `overwrite=True` is passed explicitly. This guard lives inside `save_annotation` itself (not left to callers to check first) so it can't be accidentally bypassed. When overwriting, prior `AnnotatedFeature` rows for the SERP are deleted outright and a fresh set is inserted (see the `AnnotatedFeature` table note above for why history isn't preserved here).
- Because `Feature.id` is content-addressed, inserting a `Feature` row is a get-or-create: if a row with the computed id already exists (identical `serp_id`+`type`+`content` as some earlier save), it's reused rather than re-inserted — this is also why `Feature` rows are never deleted on re-annotation (a `ParsedFeature` elsewhere might still reference the same content-addressed row).
- `get_annotation(serp_id)` returns the SERP's metadata plus its features as `AnnotatedFeatureOutput` — `id`, `type`, `xpath`, deliberately excluding `content` to keep the response lean (features can be numerous per SERP, and their content isn't always needed just to list them).
- `get_feature(feature_id)` fetches a single `Feature`'s full data (including `content`) — the way to resolve an `AnnotatedFeatureOutput.id` back to its actual markup when needed.

## Consequences

- New dependency: `sqlalchemy` (added, `~=2.0`).
- `backend/aql/models.py` (formerly `orm.py`) stays scoped to the AQL Elasticsearch mirror only, per ADR 0003. The new SQLAlchemy models live in `backend/persistence/models.py`, not there. The in-progress `AnnotatedSerp(Serp)` stub that used to sit at the end of `backend/orm.py` conflated the two concerns and has been removed from there — the SERP-annotation-record class (now named `Annotation`) is a standalone class in `persistence/models.py`, not a subtype of the AQL `Serp` document.
- `backend/namespaces.py` goes from an empty stub to holding the namespace hierarchy above.
- Because the repository module is the only thing that knows storage is local-disk-based, moving storage later (Postgres instead of SQLite, snapshots stored somewhere other than local disk, or even Elasticsearch) only touches `persistence/`'s internals and `.env` config — the SQLAlchemy models and callers stay the same. (Elasticsearch specifically was considered and set aside: it would add real operational overhead — a running server process, no embedded/zero-setup option like SQLite — for a single local annotator, and its document model doesn't map cleanly onto the relational structure here. The `persistence/` boundary keeps that option open later without paying its cost now.)

## Out of scope (deferred to later decisions)

- **Actually running a `FeatureParser` rule against SERPs and comparing results to ground truth** — this is ADR 0002's already-deferred `/validation` design pass. This ADR only decides how a parser rule's *definition* is stored, and how its output (`ParsedFeature`) is shaped, not the comparison logic itself.
- **Wiring `backend/app/routers/serps.py`'s annotation routes to `persistence/`** — implementation detail, not a new decision.
- **SQLAlchemy `relationship()` mappings between the annotation tables** — the current implementation uses plain `ForeignKey` columns and manual joins/queries; `relationship()` (with its backrefs, lazy-loading strategies, and cascade behavior) is deferred until `Session` usage feels more natural. Revisit once basic repository-function usage is comfortable.
