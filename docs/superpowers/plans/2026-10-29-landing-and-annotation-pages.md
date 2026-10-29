# Landing and annotation pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the annotation workspace and restyle the landing page so an annotator can go through a cart's SERPs, mark blocks in DevTools, categorise them, and save, in one shared style.

**Architecture:** The backend gains two routes (`GET /features/type`, `POST /serps/{id}/annotation`), and `xpath` becomes optional. The frontend gets one MUI theme, a validated landing page that passes the cart to the workspace through router state, pure DOM and keyboard helpers (unit-tested with Vitest), and workspace components wired together in `AnnotationPage`.

**Tech Stack:** FastAPI, SQLAlchemy, pytest + FastAPI `TestClient` (new); React 19, MUI 9, react-router 7, axios, Vitest + jsdom (new).

**Spec:** `docs/superpowers/specs/2026-10-29-landing-and-annotation-pages-design.md`

## Global Constraints

- Order of work: database → backend → frontend (one concept at a time, user preference).
- Collaboration is hybrid: Claude writes plumbing. Steps marked **(you write)** carry a real decision and are handed to the user as a single `TODO(human)`. Only one `TODO(human)` may exist in the code at a time.
- No commit trailers (`Co-Authored-By`, `Claude-Session`) in this repo.
- Use MUI components only; no second UI library. One theme file: `frontend/src/theme.ts`.
- Exactly one primary (contained, blue) button per page: "Start annotating" and "Save and next". Every other button uses `variant="outlined"`.
- No `alert()` or `confirm()`. Errors are red inline text. The one confirmation (No blocks with accepted blocks) is an MUI `Dialog`.
- Sentence case for all labels. MUI uppercases buttons by default, so the theme must set `typography.button.textTransform: "none"`.
- `batch_size` stays 25.
- Keyboard shortcuts: `1` Skip, `2` Accept block, `3` Save and next, `4` No blocks. They never fire while focus is in an `input`, `textarea`, `select` or contenteditable element.
- Each saved block: `type` = feature type id, `content` = marked element's `outerHTML` without the `fb-testing` / `fb-accepted` classes and without the `data-fb-index` attribute, `xpath` = `null`.
- Marking command, shown verbatim: `$0.classList.add('fb-testing')`
- Backend runs on `http://localhost:8000`, frontend on `http://localhost:5173` (CORS already allows it).

## Review Focus

1. **A SERP where two elements carry `fb-testing`** (annotator forgot to accept one): Accept must refuse with "Mark only one block at a time." and must not pick one silently. Test in Task 5.
2. **The same element accepted twice** (annotator re-runs the command on an accepted block, so it has both classes): Accept refuses with "This block is already accepted." Test in Task 5.
3. **Focus inside the SERP iframe** (the annotator clicked the page): `keydown` doesn't bubble out of an iframe, so the shortcuts must also be attached to the iframe's document. Manual check in Task 6, step "Verify in the browser".
4. **Pressing `3` twice quickly, or Save while a save is running**: only one `POST` goes out. The handlers ignore input while `busy` is true. Manual check in Task 6.
5. **Taxonomy id `"travel-related_features "` has a trailing space** in `serp_features_taxonomy.json`: `load_feature_types()` strips ids and labels so a stray space never ends up in `feature.type`. Test in Task 2.

---

### Task 1: Make `xpath` optional and add backend tests

**Files:**
- Modify: `backend/schemas.py` (`AnnotatedFeatureInput`, `AnnotatedFeatureOutput`)
- Modify: `backend/persistence/models.py:46` (`AnnotatedFeature.xpath`)
- Modify: `backend/pyproject.toml` (dev dependencies, pytest settings)
- Create: `backend/tests/conftest.py`
- Test: `backend/tests/test_annotations.py`

**Interfaces:**
- Produces: `AnnotatedFeatureInput(type: str, content: str, xpath: str | None = None)`; `AnnotatedFeature.xpath: Mapped[str | None]`; pytest fixtures `client` (a `TestClient` with lifespan run) and `cart_id` (a `UUID` of a freshly inserted `Cart`).

- [ ] **Step 1: Add the test tooling.** Run `cd backend && uv add --dev pytest httpx`. Add to `pyproject.toml`:

```toml
[tool.pytest.ini_options]
pythonpath = ["."]
testpaths = ["tests"]
```

- [ ] **Step 2: Write `tests/conftest.py`.** Before any app import, set `os.environ["APP_ENV"] = "test"` and `os.environ["PERSISTENCE_DATA_PATH"]` to a fresh `tempfile.mkdtemp()`. This way the shared `config` singleton points at a throwaway database and never at `data/test` or `data/prod`. Fixture `client`: `with TestClient(app) as c: yield c` (the `with` runs the lifespan, which calls `create_all`). Fixture `cart_id`: insert `Cart(provider="google", language="en", year=2012, created_by="pytest")` with `SessionLocal` and return its id. It depends on `client`, so the tables exist.

- [ ] **Step 3: Write the failing test**

```python
def test_save_annotation_stores_null_xpath(client, cart_id):
    serp_id = uuid4()
    save_annotation(serp_id, cart_id, [AnnotatedFeatureInput(type="carousel", content="<div>x</div>")])
    with SessionLocal() as session:
        row = session.query(AnnotatedFeature).filter_by(annotated_serp_id=serp_id).one()
    assert row.xpath is None
```

- [ ] **Step 4: Run it to verify it fails**

Run: `cd backend && uv run pytest tests/test_annotations.py -v`
Expected: FAIL with a `TypeError` about the missing `xpath` argument.

- [ ] **Step 5: Make `xpath` optional.** Use `xpath: str | None = None` in both dataclasses, and `xpath: Mapped[str | None]` on `AnnotatedFeature`.

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd backend && uv run pytest -v`
Expected: PASS

- [ ] **Step 7: Recreate the local test database.** `create_all` doesn't alter existing tables. Delete `data/test/annotator.db` (test data only; check with the user first if it holds anything they want to keep). Check whether `data/prod/annotator.db` exists; if it does, stop and ask the user.

- [ ] **Step 8: Commit**

```bash
git add backend/schemas.py backend/persistence/models.py backend/pyproject.toml backend/uv.lock backend/tests
git commit -m "Make annotated feature xpath optional; add backend tests"
```

### Task 2: `GET /features/type`

**Files:**
- Create: `backend/feature_types.py` (next to `candidate_serps.py`, which also reads a file in `resources/`. This is a plan call; it settles the planned-features "where file readers live" question for this file only.)
- Modify: `backend/schemas.py` (add `FeatureType`)
- Modify: `backend/app/routers/features.py` (currently empty)
- Modify: `backend/app/main.py` (register router)
- Test: `backend/tests/test_features.py`

**Interfaces:**
- Produces: `@dataclass FeatureType(id: str, label: str)`; `load_feature_types() -> list[FeatureType]`; `GET /features/type` → `200`, JSON `[{"id": str, "label": str}, ...]`, in file order. Only `id` and `label` are returned, because the panel shows labels and saves ids (plan call; the full file isn't needed).

- [ ] **Step 1: Write the failing tests**

```python
def test_feature_types_lists_taxonomy(client):
    response = client.get("/features/type")
    assert response.status_code == 200
    body = response.json()
    assert len(body) == 26
    assert body[0] == {"id": "exploration_features", "label": "Exploration Features"}

def test_feature_type_ids_have_no_stray_spaces(client):
    ids = [t["id"] for t in client.get("/features/type").json()]
    assert "travel-related_features" in ids
    assert all(i == i.strip() for i in ids)
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd backend && uv run pytest tests/test_features.py -v`
Expected: FAIL with 404 Not Found.

- [ ] **Step 3: Implement `load_feature_types() -> list[FeatureType]` in `backend/feature_types.py`.** Read `resources/serp_features_taxonomy.json` on each call (the file is small; no caching needed). Take `categories[*].id` and `.label`, `.strip()` both. Add the `/features` router with `prefix="/features", tags=["features"]` and `@router.get("/type")`, then `include_router` it in `main.py`.

- [ ] **Step 4: Run all backend tests**

Run: `cd backend && uv run pytest -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/feature_types.py backend/schemas.py backend/app backend/tests
git commit -m "Add GET /features/type"
```

### Task 3: `POST /serps/{id}/annotation`

**Files:**
- Modify: `backend/app/routers/serps.py`
- Test: `backend/tests/test_save_annotation_route.py`

**Interfaces:**
- Consumes: `save_annotation(serp_id, cart_id, input_features)`, `AnnotationInput(cart_id: UUID, features: list[AnnotatedFeatureInput])` (already in `schemas.py`), fixtures `client` and `cart_id`.
- Produces: `POST /serps/{serp_id}/annotation` with body `{"cart_id": str, "features": [{"type", "content", "xpath": null}]}` → `204` on success, `409` if already annotated, `404` if `cart_id` doesn't exist. An empty `features` list saves an empty annotation ("No blocks").

- [ ] **Step 1: Write the failing tests**

```python
def test_save_annotation_route(client, cart_id):
    r = client.post(f"/serps/{uuid4()}/annotation", json={"cart_id": str(cart_id), "features": [{"type": "carousel", "content": "<div>x</div>", "xpath": None}]})
    assert r.status_code == 204

def test_no_blocks_saves_empty_annotation(client, cart_id):
    serp_id = uuid4()
    r = client.post(f"/serps/{serp_id}/annotation", json={"cart_id": str(cart_id), "features": []})
    assert r.status_code == 204
    with SessionLocal() as session:
        assert session.get(Annotation, serp_id) is not None

def test_second_save_is_conflict(client, cart_id):
    serp_id, body = uuid4(), {"cart_id": str(cart_id), "features": []}
    client.post(f"/serps/{serp_id}/annotation", json=body)
    assert client.post(f"/serps/{serp_id}/annotation", json=body).status_code == 409

def test_unknown_cart_is_not_found(client):
    r = client.post(f"/serps/{uuid4()}/annotation", json={"cart_id": str(uuid4()), "features": []})
    assert r.status_code == 404
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd backend && uv run pytest tests/test_save_annotation_route.py -v`
Expected: FAIL with 405 Method Not Allowed.

- [ ] **Step 3: Add the route skeleton (Claude).** Add `@router.post("/{serp_id}/annotation", status_code=204) def create_annotation(serp_id: UUID, annotation: AnnotationInput) -> None` in `serps.py`, calling `save_annotation(serp_id, annotation.cart_id, annotation.features)`.

- [ ] **Step 4: Error → HTTP status mapping (you write).** Leave one `TODO(human)` inside `create_annotation`. The user maps `AnnotationExistsError` → `HTTPException(409)` and an unknown cart → `404`. The unknown cart surfaces as SQLAlchemy `IntegrityError` from the foreign key, because `PRAGMA foreign_keys=ON`. Whether to catch it or check the cart first is the user's choice. Follow the `try`/`except` style of `get_serp` above it.

- [ ] **Step 5: Run all backend tests**

Run: `cd backend && uv run pytest -v`
Expected: PASS (all tests from Tasks 1–3)

- [ ] **Step 6: Commit and update docs.** Tick items 1 and 3 in `docs/planned-features.md`, and tick the tests line partially ("started in `backend/tests/`").

```bash
git add backend docs/planned-features.md
git commit -m "Add POST /serps/{id}/annotation"
```

### Task 4: Shared theme and landing page

**Files:**
- Modify: `frontend/package.json` (add `vitest`, `jsdom` dev deps; `"test": "vitest run"`)
- Modify: `frontend/vite.config.ts` (`test: { environment: "jsdom" }`, with `/// <reference types="vitest/config" />`)
- Create: `frontend/src/theme.ts`
- Modify: `frontend/src/main.tsx` (wrap in `ThemeProvider` + `CssBaseline`)
- Create: `frontend/src/pages/landingForm.ts`
- Test: `frontend/src/pages/landingForm.test.ts`
- Create: `frontend/src/types/workspace.ts`
- Modify: `frontend/src/components/Selector.tsx` (add `error?: boolean`, passed to `FormControl`)
- Modify: `frontend/src/pages/LandingPage.tsx`

**Interfaces:**
- Produces:
  - `theme` (MUI `Theme`): `palette.background.default` light grey, `shape.borderRadius: 8`, `typography.button.textTransform: "none"`, `MuiButton` `disableElevation: true`, `MuiCard` `variant: "outlined"` by default.
  - `type CartForm = { provider: string; language: string; year: string; createdBy: string }` and `missingFields(form: CartForm): (keyof CartForm)[]` (a field counts as missing when it's empty after `trim()`).
  - `type WorkspaceState = { serpIds: string[]; provider: string; language: string; year: number }`, passed as router state to `/workspace/:cartId`.

- [ ] **Step 1: Install Vitest.** Run `cd frontend && npm install -D vitest jsdom` (Vitest 5 supports Vite 8). Add the `test` script and vite config entry.

- [ ] **Step 2: Write the failing test**

```ts
test("reports empty and whitespace-only fields", () => {
  expect(missingFields({ provider: "Google", language: "", year: "2012", createdBy: "  " }))
    .toEqual(["language", "createdBy"]);
});
test("reports nothing when all fields are filled", () => {
  expect(missingFields({ provider: "Google", language: "English", year: "2012", createdBy: "hurjiang" })).toEqual([]);
});
```

- [ ] **Step 3: Run it to verify it fails**

Run: `cd frontend && npm test`
Expected: FAIL, `missingFields` not found.

- [ ] **Step 4: Implement `missingFields` in `landingForm.ts`, the theme, and the landing page.** The page copy is fixed by the spec:
  - Title "AQL SERP annotation"
  - Subtitle "Choose which SERPs to annotate in this sitting."
  - Field labels "Provider", "Language", "Year", "Your name"
  - Hint "You'll get up to 25 SERPs you haven't annotated yet."
  - Button "Start annotating" (contained, full width, `ArrowForward` end icon)
  - No match: "No SERPs match these choices. Try a different year."
  - Request failed: "Couldn't create a cart. Check that the backend is running, then try again."

  Missing fields get `error` set and the submit stops. Errors show as `Typography color="error"` under the button and clear when a field changes. Center the card (`maxWidth: 380`) on the page background. On success: `navigate(`/workspace/${id}`, { state: { serpIds, provider, language, year } })`. Remove the `console.log` calls and the `// what's this?` / required-fields comments, since this task answers them.

- [ ] **Step 5: Run tests, type check, and lint**

Run: `cd frontend && npm test && npm run build && npm run lint`
Expected: all pass, no type errors.

- [ ] **Step 6: Verify in the browser.** Start both servers. Submit an empty form: four fields turn red and no request is sent (check the network panel). Submit a combination with no candidates: the red message appears and there's no popup. Submit a valid combination: the URL changes to `/workspace/<id>`.

- [ ] **Step 7: Commit**

```bash
git add frontend
git commit -m "Shared MUI theme; validate the landing page and pass the cart on"
```

### Task 5: Workspace helpers (DOM and keyboard)

**Files:**
- Create: `frontend/src/workspace/blocks.ts`
- Create: `frontend/src/workspace/shortcuts.ts`
- Test: `frontend/src/workspace/blocks.test.ts`, `frontend/src/workspace/shortcuts.test.ts`

**Interfaces:**
- Produces:
  - `type MarkResult = { element: Element } | { error: string }`
  - `findMarkedElement(doc: Document): MarkResult`. Errors, verbatim:
    - "Mark a block in DevTools first." (none marked)
    - "Mark only one block at a time." (more than one)
    - "This block is already accepted." (the element also has `fb-accepted`)
  - `markAccepted(element: Element, index: number): void`: removes `fb-testing`, adds `fb-accepted`, sets `data-fb-index`.
  - `unmarkAccepted(doc: Document, index: number): void`: removes `fb-accepted` and `data-fb-index` from the element with that index.
  - `blockContent(element: Element): string`: `outerHTML` of a clone without `fb-testing`, `fb-accepted` or `data-fb-index`. It removes an emptied `class` attribute entirely.
  - `injectOutlineStyles(doc: Document): void`: adds one `<style id="fb-annotation-styles">` (orange `#EF9F27` 2px outline for `.fb-testing`, quieter 2px dashed outline for `.fb-accepted`). Calling it twice adds only one style tag.
  - `type ShortcutAction = "skip" | "accept" | "save" | "noBlocks"` and `shortcutFor(event: KeyboardEvent): ShortcutAction | null`, with keys `1`/`2`/`3`/`4`. It returns `null` when the target is an `input`/`textarea`/`select`/contenteditable element, or when a modifier (ctrl/meta/alt) is held.

- [ ] **Step 1: Write the failing tests.** Build documents with `document.implementation.createHTMLDocument()`.

```ts
test("finds the single marked element", () => { /* one .fb-testing → { element } */ });
test("refuses when nothing is marked", () => { expect(findMarkedElement(doc)).toEqual({ error: "Mark a block in DevTools first." }); });
test("refuses two marked elements", () => { expect(findMarkedElement(doc)).toEqual({ error: "Mark only one block at a time." }); });
test("refuses an already accepted element", () => { /* class="fb-accepted fb-testing" */ expect(findMarkedElement(doc)).toEqual({ error: "This block is already accepted." }); });
test("blockContent strips annotation marks", () => {
  // <div class="kp fb-accepted" data-fb-index="1"><b>x</b></div>
  expect(blockContent(el)).toBe('<div class="kp"><b>x</b></div>');
});
test("blockContent drops an emptied class attribute", () => { expect(blockContent(onlyFbEl)).toBe("<div>y</div>"); });
test("markAccepted then unmarkAccepted restores the element", () => { /* classes and data-fb-index back to original */ });
test("injectOutlineStyles is idempotent", () => { injectOutlineStyles(doc); injectOutlineStyles(doc); expect(doc.querySelectorAll("#fb-annotation-styles")).toHaveLength(1); });
```

```ts
test("maps 1-4 to actions", () => { expect(shortcutFor(key("3"))).toBe("save"); expect(shortcutFor(key("4"))).toBe("noBlocks"); });
test("ignores keys typed in a text field", () => { expect(shortcutFor(key("1", inputElement))).toBeNull(); });
test("ignores keys with modifiers", () => { expect(shortcutFor(key("2", body, { metaKey: true }))).toBeNull(); });
test("ignores other keys", () => { expect(shortcutFor(key("5"))).toBeNull(); });
```

- [ ] **Step 2: Run them to verify they fail**

Run: `cd frontend && npm test`
Expected: FAIL, modules not found.

- [ ] **Step 3: Implement `blocks.ts` and `shortcuts.ts`** to the interfaces above.

- [ ] **Step 4: Run tests and type check**

Run: `cd frontend && npm test && npm run build`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add frontend/src/workspace
git commit -m "Add workspace helpers for marked blocks and shortcuts"
```

### Task 6: Annotation workspace

**Files:**
- Create: `frontend/src/api/features.ts`, `frontend/src/api/serps.ts`
- Modify: `frontend/src/types/workspace.ts` (add the types below)
- Create: `frontend/src/components/workspace/TopBar.tsx`, `SerpFrame.tsx`, `StepPanel.tsx`, `DoneCard.tsx`
- Modify: `frontend/src/pages/AnnotationPage.tsx`

**Interfaces:**
- Consumes: Task 2 and 3 routes; `WorkspaceState`; everything from Task 5.
- Produces:
  - `type FeatureType = { id: string; label: string }`
  - `type AcceptedBlock = { index: number; type: string; label: string; content: string }`
  - `type AnnotatedFeatureInput = { type: string; content: string; xpath: string | null }`
  - `getFeatureTypes(): Promise<FeatureType[]>`
  - `getSerpHtml(serpId: string): Promise<string>` (axios `responseType: "text"`)
  - `saveAnnotation(serpId: string, cartId: string, features: AnnotatedFeatureInput[]): Promise<void>`
  - `TopBar({ position, total, provider, language, year, onExit })`, where `position` is 1-based. It shows "SERP {position} of {total}", a thin `LinearProgress` (`variant="determinate"`), "{provider} · {language} · {year}", and an outlined "Exit" button.
  - `SerpFrame({ html, error, onReady })`: renders `<iframe srcDoc={html}>` with no `sandbox` attribute. On load it calls `onReady(iframe.contentDocument)`. Shows `error` in red instead of the iframe when set.
  - `StepPanel({ blockNumber, featureTypes, selectedType, onSelectType, onAccept, accepted, onRemove, onSave, onNoBlocks, onSkip, message, busy })`
  - `DoneCard({ total, onBack })`: "All {total} done" and an outlined "Back to start" button.

- [ ] **Step 1: API, types and components (Claude).** Build the layout from the approved mockup. Use a full-height column: `TopBar`, then a row of `SerpFrame` (`flex: 1`) and `StepPanel` (width 360). The panel copy, verbatim:
  - Heading "Feature block #{n}"
  - "1. Mark it in DevTools", followed by the command in monospace with a copy `IconButton` (`navigator.clipboard.writeText`)
  - "2. Choose a category" (2-column grid of outlined buttons; the selected one gets `color="primary"` and a tinted background, not `contained`)
  - "Accept block" (outlined)
  - "Accepted on this SERP ({count})" with rows "#{index} {label}", each with a close `IconButton` labelled "Remove"
  - "Save and next" (contained)
  - "No blocks", "Skip" (outlined)

  Each shortcut key is shown as a small `kbd` after its label. The panel scrolls on its own if the category list is long.

- [ ] **Step 2: Page state and plumbing (Claude).** In `AnnotationPage`:
  - Read `cartId` (`useParams`) and `state` (`useLocation().state as WorkspaceState | null`). Without state, show the shared card style with "This cart isn't open in this tab anymore. Start a new one from the landing page." and a link to `/`.
  - Hold `position`, `html`, `serpError`, `featureTypes`, `selectedType`, `accepted`, `message`, `busy`, and a ref to the iframe document.
  - Load feature types once. On each `position` change, fetch the SERP HTML: a 404 or 502 sets `serpError` to "This SERP couldn't be loaded. Skip it to continue.". Reset `accepted`, `selectedType` and `message`.
  - In `onReady`, call `injectOutlineStyles`, and add the `keydown` listener to both `window` and the iframe document, removing both on change and unmount.
  - Accept uses `findMarkedElement` → `markAccepted` → append to `accepted` (the index is one more than the highest accepted index) → clear `selectedType`. With no category chosen, it sets `message` to "Choose a category first.".
  - Remove calls `unmarkAccepted`.
  - Exit navigates to `/`. After the last SERP, render `DoneCard`.

- [ ] **Step 3: Save, No blocks and Skip behaviour (you write).** Leave one `TODO(human)` for the three handlers `handleSave`, `handleNoBlocks` and `handleSkip`. The behaviour is fixed by the spec:
  - Save with no accepted blocks shows "No blocks accepted. Use No blocks if this SERP has none." and doesn't save.
  - No blocks with accepted blocks opens the confirm `Dialog` ("Throw away {n} accepted blocks and save this SERP as having none?", buttons "Cancel" / "Save as no blocks").
  - Skip saves nothing.
  - A 409 response moves on to the next SERP.
  - Any other failure keeps `accepted`, shows "Saving failed. Your blocks are kept. Try again.", and stays on the SERP.
  - All three ignore calls while `busy`, and set `busy` around the request.

  How to structure it (one shared `advance()`, how to detect 409 with `axios.isAxiosError`) is the user's call.

- [ ] **Step 4: Type check, lint and tests**

Run: `cd frontend && npm test && npm run build && npm run lint`
Expected: all pass.

- [ ] **Step 5: Verify in the browser** with both servers running (`APP_ENV=test`) and a cart from the test candidate file:
  - The top bar shows "SERP 1 of N" and the provider, language and year.
  - Mark a block in DevTools inside the iframe: the orange outline appears.
  - Choose a category and accept: the outline turns dashed and the row appears.
  - Remove that row: the outline goes away.
  - Mark two blocks and accept: the message appears.
  - Click inside the SERP, then press `2`: Accept still fires (Review Focus 3).
  - Press `3` twice quickly: the network panel shows one POST (Review Focus 4).
  - No blocks with an accepted block: the dialog appears.
  - Skip: no POST is sent.
  - Stop the backend and Save: the error appears and the blocks stay.
  - Finish the cart: "All N done".
  - Reload `/workspace/<id>`: the "isn't open in this tab" card appears.
  - Check that `annotated_feature.xpath` is `NULL` in `data/test/annotator.db`.

- [ ] **Step 6: Commit and update docs.** Tick item 6 in `docs/planned-features.md`.

```bash
git add frontend docs/planned-features.md
git commit -m "Build the annotation workspace"
```
