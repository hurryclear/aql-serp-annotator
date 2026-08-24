# Understanding FastAPI's `lifespan`

This note walks through `app/main.py`'s `lifespan` function — what problem it solves, and why it's shaped the way it is. Written while wiring up SQLite storage per [ADR 0004](../adr/0004-local-annotation-storage.md).

## The problem: "run this once, at startup"

`persistence.py` defines five SQLAlchemy model classes (`AnnotatedSerp`, `Feature`, ...), but defining a Python class doesn't create a database table — something has to actually run `CREATE TABLE` statements against the SQLite file, once, when the app starts.

We don't want that to happen as a side effect of just *importing* `persistence.py` (import-time side effects — like touching the filesystem — are surprising and make code harder to test and reason about). We want it to happen explicitly, tied to "the app is starting up."

FastAPI's answer to "run code once at startup, and optionally once at shutdown" is `lifespan`.

## Background: what "async" means here

Normal ("sync") code runs one instruction at a time, and each one waits for the previous to fully finish. Imagine one cashier serving one customer start-to-finish — scan items, wait for the card to process, bag groceries, hand over the receipt — before even looking at the next person in line. If the card takes 5 seconds, the cashier just stands there, idle.

Async code can avoid that idle-waiting: instead of standing there while the card processes, an async cashier sets that transaction aside as "waiting," starts ringing up the next customer, and comes back to finish the first one once their card clears. One cashier, handling multiple customers concurrently, by working on whatever's currently ready instead of blocking on whatever's currently slow.

Web servers face exactly this problem — while one request is waiting on a slow network call or database query, the server could be making progress on a different request instead of sitting idle. FastAPI is built async for this reason.

Two keywords come with this:

- `async def` marks a function as one that's *allowed* to pause and resume like this.
- `await` marks the specific point inside such a function where "pause here, resume when this is ready" actually happens.

**Important nuance for our case:** `Base.metadata.create_all(...)` is an ordinary, blocking, synchronous call — it doesn't use `await` at all, it just runs top-to-bottom like any normal function call. The *only* reason `lifespan` has to be declared `async def` is that FastAPI's internal machinery expects to call it that way — it's a requirement of the interface, not something our own code needs. We're filling a required async-shaped slot with one plain synchronous line inside it, not writing genuinely-concurrent logic.

## Background: context managers and `yield`

You've likely seen this shape before: `with open(file) as f: ...` — code that runs some setup (open the file), gives you something to work with, and then automatically runs cleanup (close the file) when the `with` block ends. That's a *context manager*.

FastAPI needs exactly that bracket shape for the whole app's lifetime: something that runs once when the server starts, and (optionally) something that runs once when it shuts down.

Normally, building a context manager means writing a class with `__enter__`/`__exit__` methods (or `__aenter__`/`__aexit__` for the async version). The `@asynccontextmanager` decorator (from `contextlib`) lets you skip that — you write one `async def` function containing a single `yield`, and Python turns it into a proper async context manager for you.

The `yield` is the pivot point:

- Everything **before** `yield` runs once, at startup.
- Execution then **pauses** at `yield` — this is where FastAPI actually serves requests, for the app's entire running lifetime.
- Everything **after** `yield` (if anything) runs once, at shutdown.

## Walking through our code

```python
from fastapi import FastAPI
from contextlib import asynccontextmanager
from persistence import Base, config


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(config.persistence.sqlite_engine)
    yield


app = FastAPI(lifespan=lifespan)
```

- `from persistence import Base, config` — reuses the *same* `Base` (which has all five model classes registered on its `.metadata`) and the *same* `config` instance (and therefore the same `sqlite_engine`) that `persistence.py` already built. We don't construct a second `Config()` here — that would build a second, separate engine, breaking the "one engine, shared everywhere" idea.
- `@asynccontextmanager` turns the function below it into something FastAPI can use as a lifespan handler.
- `async def lifespan(app: FastAPI):` — the `app` parameter is required by FastAPI's calling convention, even though the body never uses it.
- `Base.metadata.create_all(config.persistence.sqlite_engine)` — walks the auto-collected catalog of every `Base` subclass's table definition, and creates any table that doesn't already exist in the SQLite file. Tables that already exist are left alone, so this is safe to run on every startup, not just the first.
- `yield` — hands control over to the running app. Nothing needs to happen at shutdown yet, so nothing comes after it.
- `app = FastAPI(lifespan=lifespan)` — passes the *function itself* (not a call to it) so FastAPI knows to run it as part of the app's start/stop cycle.

## Why this matters beyond just "getting it to work"

This pattern — `Engine` built once in `config.py`, tables created once at startup via `lifespan`, short-lived `Session`s per request/operation afterward — mirrors a general shape you'll see in most web backends: expensive, long-lived resources (connections, engines, pools) get set up once at process start, while per-request work stays cheap and short-lived.
