# AQL SERP Annotator

## Frontend

```zsh
cd frontend
npm install # for first time
npm run dev
```

## Database: SQLite, SQLAlchemy

- Tradeoff: it handles only one write at a time.

## Backend

```zsh
cd backend
uv run uvicorn app.main:app --reload
```

### Environments: test and prod

`APP_ENV` picks where data goes ([ADR 0006](docs/adr/0006-test-and-prod-environments.md)). It defaults to `test`.

| `APP_ENV` | Local data | Candidate SERPs |
|---|---|---|
| `test` | `data/test/` | `resources/candidate_serps_test.jsonl` |
| `prod` | `data/prod/` | `resources/candidate_serps.jsonl` |

For real annotation, put `APP_ENV=prod` in `backend/.env`, or run once in prod:

```zsh
APP_ENV=prod uv run uvicorn app.main:app --reload
```

The startup log shows which environment is running (`APP_ENV=… · data: …`).

Planned work is tracked in [docs/planned-features.md](docs/planned-features.md).
