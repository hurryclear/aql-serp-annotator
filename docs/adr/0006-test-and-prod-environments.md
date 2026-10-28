# 0006. Two environments: test and prod

Status: accepted
Date: 2026-10-28

## Context

Until now the backend had one set of local data (`data/annotator.db`, `data/annotated_serps/`) and one candidate SERPs file. Trying things out (manual `/docs` calls, smoke scripts) wrote trial carts and snapshots into the same database that real ground-truth annotations would go into, and the only way to protect real data was to remember to override paths by hand.

Other annotators will eventually run the app too, packaged as a Docker container. There is no server yet: whoever runs the app keeps its data on their own machine. A hosted server is planned, but later.

A third "dev" environment (the author annotating real data locally) was considered and folded into prod: the author's own annotations are real ground truth, so they belong with prod data, not with disposable data.

## Decision

Two environments, chosen by one setting, `APP_ENV` (`test` or `prod`):

| | `test` | `prod` |
|---|---|---|
| Purpose | automated checks, trying things out; data is disposable | real annotation, by the author or by users in a container |
| Local data | `data/test/` (`annotator.db`, `annotated_serps/`) | `data/prod/` |
| Candidate SERPs | `resources/candidate_serps_test.jsonl` (small, hand-picked) | `resources/candidate_serps.jsonl` (the real set) |
| AQL | same read-only Elasticsearch + S3 | same |

- The code is identical in both; `config.py` holds the per-environment defaults in one `ENVIRONMENTS` table, applied by a `model_validator(mode="before")` on `Config`.
- **Defaults to `test`** when `APP_ENV` is not set, so real annotations are only touched on purpose. The author's `.env` sets `APP_ENV=prod`; a future Docker image sets it too.
- Every default stays overridable (`PERSISTENCE_DATA_PATH`, `CANDIDATES_DIR_PATH`, `CANDIDATES_FILE_NAME`). That is how a container will point the database at a mounted volume, and how test scripts point at a temp folder.
- Environment variables beat `.env`, so a script can force `APP_ENV=test` even when `.env` says `prod`.
- On startup the backend logs the active environment, data folder and candidate file next to uvicorn's own startup lines.

## Consequences

- Existing `data/annotator.db` and `data/annotated_serps/` (trial carts and one bad `robots.txt` snapshot) become test data under `data/test/`; prod starts with an empty database, created with the current schema (including `parsed_feature`'s composite key).
- `POST /carts` in prod needs `resources/candidate_serps.jsonl` to exist; until the real candidate set is prepared, prod has nothing to offer.
- A typo such as `APP_ENV=staging` fails at startup with a clear validation error instead of silently using some default.

## Out of scope (deferred)

- **Docker image** for prod: Dockerfile, mounting `data/prod` as a volume, passing AQL credentials.
- **A hosted server** shared by several annotators, and with it the question of a single source of truth for annotations (one server database vs. merging local databases) and annotator identity (`created_by` is free text today).
- Backups of prod data.
