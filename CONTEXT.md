# Local Annotation & Parsing

Human-annotated ground truth and automated parser output for AQL SERPs, stored locally (SQLite + file snapshots) since AQL's Elasticsearch is read-only. See [ADR 0004](docs/adr/0004-local-annotation-storage.md).

## Language

**Annotation**:
A human's ground-truth annotation record for one AQL SERP — one per `serp_id`, tracking when it was created/last updated. Holds no SERP data itself (no query, no HTML) — it's a thin marker row; the actual annotated content lives in its `AnnotatedFeature`s. Belongs to exactly one `Cart` (the working session it was completed under), via `cart_id`.
_Avoid_: AnnotatedSerp (an earlier name — dropped for consistency with `save_annotation`/`get_annotation`, and because "SERP" in the name wrongly implied it held SERP data)

**Cart**:
A working session opened from the landing page: a human picks `provider`/`year`/`language`, and the backend resolves that into a batch of qualifying, not-yet-annotated SERP ids, returned to the frontend to work through — but not persisted as a list anywhere. Tracks who opened it (`created_by`, free text — no login system exists) and when. `Cart` itself holds only the *criteria*, not the resolved SERP ids; those live only in the frontend's memory for that sitting. Distinct from `Annotation`: a `Cart` is "a session was opened under these criteria"; an `Annotation` is "this one SERP is actually done," and points back at the `Cart` it was completed under, via `cart_id`. Closing the tab mid-session loses track of what was left unfinished in that cart — acceptable for now since nothing requires resuming one; revisit (e.g. a join table recording the offered batch) if that becomes a real need.
_Avoid_: AnnotationSession, AnnotationCart, Session, Batch, Assignment (all considered and rejected — the first two collide visually/verbally with `Annotation` since they share its exact prefix; bare `Session` collides with SQLAlchemy's own `Session` class already used throughout `persistence.py`; `Batch`/`Assignment` were just personal preference misses); CartSerp (a join table persisting the offered batch — cut because nothing needed it: the "who annotated what" goal is already answerable from `Annotation.cart_id` alone, and the batch only needs to survive in frontend memory for one sitting)

**Feature**:
A single feature-block instance: its type and the raw matched-element markup (`content`) — not the extracted answer. Shared by both human ground truth and automated parser output. Content-addressed: identical `(serp_id, type, content)` always produces the same `Feature.id`, so identical blocks are deduplicated automatically rather than stored twice. ("Feature" is the established term from the research area this project draws on — not renamed to disambiguate from the general English word, despite the overlap.)

**AnnotatedFeature**:
Links a `Feature` to the `Annotation` it was found in, plus a **rule xpath**: a general expression the human wrote (e.g. `//div[@class="kp-blk"]`) and tested, via `POST /xpath`, to confirm it extracts this exact block — not the element's absolute DOM position (a location xpath was considered and set aside: rule xpaths are what parser design needs first, and the block's location is recoverable later from `content` + the HTML snapshot if ever needed). Deliberately excludes extracted answer text/source link — ground truth here is "this feature exists at this location," not its extracted content. No history is kept across re-annotation: since `feature_id` is this table's primary key (not just a foreign key), a given `Feature` can only ever be linked by one `AnnotatedFeature` row — re-annotating deletes the SERP's old rows and inserts a fresh set, rather than trying to preserve superseded ones.

**ground truth**:
The human-annotated reference data (an `Annotation` and its `AnnotatedFeature`s) used to develop and validate automated parsers against.
