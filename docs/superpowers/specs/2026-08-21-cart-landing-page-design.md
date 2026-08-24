# Landing page + Cart creation — design spec

Companion implementation spec to [ADR 0005](../../adr/0005-cart-persisted-annotation-session.md), which records *why* this introduces a persisted session concept. This doc covers *how* to build it: the first real frontend screen, and the first real backend route, replacing the current broken/empty stubs.

## Scope

In scope:
- `POST /carts` — the only backend route this task implements.
- The landing page — a form for provider/year/language/name, wired to that route.

Out of scope (see ADR 0005's "Out of scope" section): the annotation workspace itself, S3 HTML fetching, resuming a cart, `/xpath`, `/features/type`.

## Backend

### `config.py`

Add a manifest file path, following `PersistenceConfig`'s existing style:

```python
class PersistenceConfig(BaseSettings):
    ...
    manifest_path: Path = Path(__file__).resolve().parent.parent / "data" / "serps_manifest.jsonl"
```

### `backend/manifest.py` (new)

Reads the JSONL manifest one line at a time, filtering by the three fields this task needs. Tolerant of any other fields a line might have (e.g. `query`) — read only what's needed, ignore the rest.

```python
import json
from uuid import UUID
from config import Config

config = Config()


def search_manifest(provider: str, year: int, language: str) -> list[UUID]:
    matches = []
    with config.persistence.manifest_path.open("r", encoding="utf-8") as f:
        for line in f:
            record = json.loads(line)
            if (
                record["provider"] == provider
                and record["year"] == year
                and record["language"] == language
            ):
                matches.append(UUID(record["id"]))
    return matches
```

### `backend/schemas.py`

Add the request/response DTOs for this route, alongside the existing `AnnotatedFeatureInput`/`AnnotatedFeatureOutput`:

```python
@dataclass
class CartInput():
    provider: str
    year: int
    language: str
    created_by: str
    batch_size: int = 25


@dataclass
class CartOutput():
    id: UUID | None
    serp_ids: list[UUID]
    total: int
```

`id` is nullable — a zero-match search returns `None`, since no `Cart` row gets persisted for it (per ADR 0005).

### `backend/persistence.py`

Add the `Cart` model, the `cart_id` column on `Annotation`, and a `create_cart` repository function.

```python
class Cart(Base):
    __tablename__ = "cart"
    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    provider: Mapped[str]
    year: Mapped[int]
    language: Mapped[str]
    created_by: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))


class Annotation(Base):
    __tablename__ = "annotation"
    serp_id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    cart_id: Mapped[UUID] = mapped_column(ForeignKey("cart.id"))
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(UTC))
    updated_at: Mapped[datetime] = mapped_column(
                                        default=lambda: datetime.now(UTC),
                                        onupdate=lambda: datetime.now(UTC)
                                    )
```

```python
def create_cart(input: CartInput) -> CartOutput:
    candidate_ids = search_manifest(input.provider, input.year, input.language)

    with SessionLocal() as session:
        already_annotated = {
            row.serp_id
            for row in session.query(Annotation.serp_id)
            .filter(Annotation.serp_id.in_(candidate_ids))
        }
        available_ids = [sid for sid in candidate_ids if sid not in already_annotated]
        serp_ids = available_ids[: input.batch_size]

        if not serp_ids:
            return CartOutput(id=None, serp_ids=[], total=0)

        cart = Cart(
            provider=input.provider,
            year=input.year,
            language=input.language,
            created_by=input.created_by,
        )
        session.add(cart)
        session.commit()
        session.refresh(cart)

        return CartOutput(id=cart.id, serp_ids=serp_ids, total=len(serp_ids))
```

Note: `Annotation.cart_id` requires an existing `Cart` row to reference — since `save_annotation` isn't implemented yet in this task, this column just needs to exist in the schema; wiring an actual value into it happens when the annotation workspace task adds `cart_id` to `save_annotation`'s signature (per ADR 0005).

### `backend/app/routers/carts.py` (new)

```python
from fastapi import APIRouter

from schemas import CartInput, CartOutput
from persistence import create_cart

router = APIRouter()


@router.post("/carts", tags=["carts"])
def create(input: CartInput) -> CartOutput:
    return create_cart(input)
```

A zero-match result (`total: 0`) is a normal response, not an HTTP error — the frontend distinguishes "no SERPs match" from a real failure by checking `total`, not the status code. Register the router in `backend/app/main.py` alongside (once fixed) `serps`, `xpath`, `features`.

## Frontend

No router library — `App.jsx` holds one piece of state (`result: null | CartOutput`) and conditionally renders the form or the confirmation screen.

- `SerpSelectionForm` component: three hardcoded `<select>`s (provider/year/language) + a text input (`created_by`) + submit button. `batch_size` stays fixed at the default (25), not exposed in the UI yet.
- `frontend/src/api.js` (new): one function wrapping the `fetch("/carts", {method: "POST", ...})` call, returning the parsed JSON body.
- On submit: call the API, store the result in state.
- Render: if `result === null`, show the form. If `result.total === 0`, show "No SERPs match your selection." Otherwise show the count and (as a placeholder — the workspace itself is a later task) the cart id, e.g. "Cart created: 12 SERPs ready to annotate."

Dev proxy: the frontend (Vite, port 5173) needs to reach the backend (FastAPI, typically port 8000) without a CORS error. Use Vite's dev-server proxy (`vite.config.js` → `server.proxy: {"/carts": "http://localhost:8000", ...}`) rather than adding CORS middleware to the backend — keeps `fetch("/carts")` working identically in dev, and avoids opening up CORS on a backend that (for now) has exactly one frontend consumer.

## Testing

No test infra exists in `backend/` yet. Suggested minimal check if you want one for this task: a small fixture JSONL file with a handful of known rows, and a test asserting `search_manifest` returns the expected ids for a given provider/year/language — cheap to write, and it's the one piece of new logic in this task that isn't just wiring. Not required to proceed.
