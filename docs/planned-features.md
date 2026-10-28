# Planned features

What's built, what's next, and what's waiting on a decision. One line per item; details live in the linked ADRs. When you start an item, it can become a GitHub issue (see `docs/agents/issue-tracker.md`); tick it here when it lands.

Last updated: 2026-10-28

## Next: annotation workflow (in build order)

Each step only needs the ones above it, except 5, which can go any time.

- [ ] **1. `GET /features/type`**: return the feature-type taxonomy from `resources/serp_features_taxonomy.json` (26 categories) for the workspace dropdown. File: `app/routers/features.py` (empty). Decide: full file or `id` + `label` only; call them `categories` or `feature_types` (ADR 0002 renamed the term); read once at startup or per request; where the file reader lives.
- [ ] **2. `POST /xpath`**: test a rule xpath against the SERP HTML and the clicked block; say whether it matches. Uses lxml and `utils/html_utils.normalize_html`. Stateless. File: `app/routers/xpath.py` (empty). ADR 0002.
- [ ] **3. `POST /serps/{id}/annotation`**: save an annotation through `save_annotation`. `AnnotationExistsError` → 409; decide how the client asks to overwrite; an empty feature list means "No features". File: `app/routers/serps.py`.
- [ ] **4. `GET /serps/{id}/annotation`**: new `get_annotation(serp_id)` in `persistence/annotations.py`, joining `annotated_feature` with `feature`; returns `AnnotatedFeatureOutput` items, 404 when there's no annotation.
- [ ] **5. Reject non-HTML captures**: in `aql/client.py`, raise `SerpHtmlUnavailableError` when `capture.mimetype` isn't `text/html` (seen: SERP `df324096…` is a 2001 `robots.txt` capture). Delete that cached snapshot afterwards.
- [ ] **6. Annotation workspace (frontend)**: `LandingPage` passes the cart's `serp_ids` on (navigate drops them today); `AnnotationPage` shows each SERP in an iframe, click to select a block, test its xpath, then Save / No features (empty annotation) / Skip (saves nothing).

## Candidate SERPs

- [ ] **Real candidate set**: write `resources/candidate_serps.jsonl` for prod. Until it exists, `POST /carts` in prod has nothing to offer.
- [ ] **Filter script**: query AQL (provider, year, language) and keep only annotatable SERPs: `warc_location` set, `capture.mimetype == "text/html"`, `capture.status_code == 200`. Uses `Serp.search(...).scan()` (ADR 0003). Decide whether it lives in this repo.
- [ ] **Decide: multi-language values** such as `"de+en"` and `"fr+pt"`. `search_candidate_serps` compares with exact `==`, so they never match `LANGUAGES["english"] = "en"`.
- [ ] **Decide: one provider list**. `mapping.py` and `resources/providers.json` list different providers.
- [ ] **Decide: where `candidate_serps.py` lives**: top level (today) or `persistence/` (local data access).
- [ ] Later: record which candidate-set version a `Cart` was drawn from, for traceability.

## Environments and deployment

- [x] **test and prod environments** via `APP_ENV` (ADR 0006).
- [ ] **`.env.example`**: committed list of every setting, with fake values, updated whenever a setting is added or renamed.
- [ ] **Docker image for prod**: `APP_ENV=prod`, `data/prod` on a mounted volume (`PERSISTENCE_DATA_PATH`), AQL credentials passed as env vars.
- [ ] **Hosted server** shared by several annotators. Needs decisions first: one server database vs. merging local databases (today two people can get the same SERP, because each machine only sees its own annotations), and annotator identity (`created_by` is free text).
- [ ] Backups of prod data.

## Later: needs a design decision first

- [ ] **`get_feature(id)`**: resolve a feature id back to its content (ADR 0004).
- [ ] **Parser rules**: store `FeatureParser` rules and their `ParsedFeature` output.
- [ ] **`/validation`**: compare parser output with ground truth. Open: API route or separate script (ADR 0002).
- [ ] **Ground-truth editing**: review mismatches and correct annotations.
- [ ] **Resume an unfinished cart**: would need the offered batch persisted (a `CartSerp` table, cut for now; ADR 0005).
- [ ] **`tests/` folder**: turn the smoke checks (shared config, carts, annotations, snapshots, environment isolation) into a pytest suite.

## Done

- [x] `POST /carts`: random batch of not-yet-annotated candidate SERPs, saved as a `Cart` (ADR 0005).
- [x] `GET /serps/{id}`: snapshot cache, else AQL fetch + clean + save (ADR 0003, 0004).
- [x] `save_annotation()`: function only; step 3 adds its route.
- [x] SQLite schema: six tables, foreign keys enforced, composite key on `parsed_feature`.
- [x] Backend layout: `persistence/`, `aql/`, `resources/`; one shared `config`.
- [x] "Manifest" renamed to candidate SERPs; candidate files tracked in `resources/`.
