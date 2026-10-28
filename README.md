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
