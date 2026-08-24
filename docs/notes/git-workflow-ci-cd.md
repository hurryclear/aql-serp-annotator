# Git workflow, CI/CD, and Docker — where we stand

Notes from a conversation about how to manage git going forward, once we noticed everything since the initial commit was sitting uncommitted, unbranched, on `main`.

## Starting point

- `main` had exactly one commit (`f2e0590 init commit`). Everything built since — `backend/`, `docs/`, `src/`, `data/`, plus `.gitignore` edits — was untracked/unstaged, directly on `main`.
- A remote branch `claude/fastapi-python-backend-c1bcaf` exists, unmerged into `main`, likely leftover from an earlier cloud Claude Code session. Not investigated further — worth checking what's on it before deciding to keep or delete it.

## A real bug to fix before any commit

`data/annotator.db` is untracked but **not covered by `.gitignore`**. ADR 0004 says the SQLite file and snapshot directory should be gitignored (generated data, not source), but `.gitignore` has no `data/` entry yet. If `git add -A`/`git add .` is ever run, this generated `.db` file (and future HTML snapshots) would get committed by accident. `backend/.env` is already correctly ignored, by contrast — just `data/` is missing.

**Fix:** add a `data/` entry to `.gitignore`.

## Can I branch and commit now?

Yes. Since `main` only has the init commit and everything since is uncommitted and unbranched, nothing is lost by branching now — `git checkout -b <name>` just gives the current uncommitted work a home other than `main`.

## Recommended workflow (solo/learning project, no CI yet)

Lightweight, trunk-based — not full GitFlow:

- `main` = the branch that's supposed to always work. Nothing gets committed to it directly.
- Work happens on short-lived feature branches, one per ADR or per logical unit of work (matches this repo's existing ADR-driven structure) — e.g. `annotation-storage` for finishing `persistence.py`'s repository functions, rather than one branch per tiny change.
- Merge back into `main` once a unit of work is done and manually verified.
- Since there's no CI yet, "always works" on `main` is enforced manually: actually run the app / hit the endpoints before merging — e.g. the way we ran `lifespan` end-to-end and checked the SQLite tables got created, after wiring it up.

**Splitting the current uncommitted pile into commits**, since it spans genuinely separate concerns:
- `.gitignore` fix (add `data/`).
- `docs/adr/*` + `docs/notes/*` — separable from code.
- `backend/` — the new FastAPI backend. Could split further: "AQL ES/S3 mirror" (`orm.py`) vs. "local annotation storage" (`config.py`, `persistence.py`, `namespaces.py`, `main.py` lifespan wiring), for finer history.
- `src/` — the pre-migration Flask codebase (per ADR 0001). Worth its own commit, separate from new backend work, so history clearly shows "here's the old code, here's the new code."

## When to set up CI

**Soon, not now** — trigger point: once `persistence.py`'s repository functions exist with at least one test (e.g. a save→get round-trip for `save_serp_html`/`get_serp_html`). Not "when the whole backend is done," and not "when there's full coverage" — just once there's something meaningful to check.

A minimal GitHub Actions workflow is enough to start: `uv run pytest` on PRs into `main`, maybe a lint step.

## When to set up CD and Docker

**Not yet.** There's no deployment target defined yet — still local SQLite + local dev, no Docker, no hosting decision made. Setting up CD now would mean automating deployment to nowhere. Revisit once Docker and a real hosting target exist — likely once the backend and frontend are both functional enough to actually deploy.

## Suggested order, overall

1. Fix `.gitignore` (add `data/`).
2. Branch workflow — start committing on feature branches instead of unbranched on `main`. *(in progress)*
3. First tests — e.g. a round-trip test once `persistence.py`'s repository functions exist.
4. CI — lint + test on PRs into `main`.
5. Docker — once there's a real deployment target.
6. CD.
