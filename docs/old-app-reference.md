# Old app reference: features and API

What the old Flask annotator in `src/` could do, and the HTTP API it used to do it. This is the feature list the new FastAPI + React app (`backend/`, `frontend/`) is catching up to. It describes the old code as it is; it is not a design for the new API.

Last checked against `src/`: 2026-10-30

## Words used here

- **FB (feature block)**: one block on a SERP that belongs to a feature category, e.g. a knowledge panel or a "People also ask" box.
- **GT (ground truth)**: the annotated SERP HTML, treated as the correct answer.
- **pyl**: provider + year + language, e.g. `google-2012-en`. The old app grouped everything by pyl.
- **Parser**: code that extracts FBs from a SERP with XPath rules. Validation compares its output with GT.

## Part 1: Features

The old app was two separate tools: the **annotator** (`src/annotation/`) and the **GT editor** (`src/validation/`).

### 1. Annotator

**Start a session (command line).** `run_server.py --provider --year --lang --batch --port` starts the server for one pyl. It reads a cached list of SERP ids for that pyl, removes the ones already annotated, and keeps the first `batch` (default 20). There is one session per server process; to change pyl you restart the server.

**Setup screen.** Shows the session: provider, year, language, batch size. A "Start Annotation" button opens the workspace.

**View a SERP.** Each SERP loads in an iframe, fetched from AQL (Elasticsearch for metadata, S3 WARC for the HTML). Before display the HTML is cleaned:
- `<script>`, `<noscript>`, inline `on…=` handlers and `<meta http-equiv=refresh>` are removed;
- a `<base href>` is added so relative links and images resolve to the original site;
- CSS hides popups, cookie banners, modals and spinners.

A **"Raw SERP"** checkbox reloads the iframe with the uncleaned HTML.

**Progress bar.** Shows "Progress: n / total" and the current SERP id.

**Annotate one FB (repeat per block).**
1. *Mark*: in DevTools, select the element and run `$0.classList.add('fb-testing')`. It gets an orange outline.
2. *Category*: click one of the category buttons. Buttons come from the taxonomy, sorted alphabetically in groups (C | D–P | R–W), with the "pack" categories (image pack, knowledge panel, local pack) kept together and `placeholder` last. Hovering shows the category description.
3. *XPath (optional, hidden in the UI)*: type an XPath, or pick one from a list of existing XPaths for that category, and press "Test XPath". The result says Match / Mismatch / Error, with a "Show details" toggle that shows the marked HTML next to the HTML the XPath found. XPaths that matched are listed as "Working XPaths". An "LLM XPath generator" button was planned but never built.
4. *Accept*: "Accept & Next FB" turns the element green (`fb-accepted`), stores `data-fb-index`, `data-fb-category` on it, and adds it to the "Accepted FBs" list. The FB counter goes up by one.

**Finish a SERP.**
- **Save & Next**: needs at least one accepted FB and a confirm dialog. Turns every `fb-accepted` into `fb`, sends the whole iframe HTML to the server, and loads the next SERP.
- **Skip (No FB)**: sends the HTML with no FBs. The server still records the SERP as done, so it is not offered again. (In the new app this is "No blocks"; the new "Skip" saves nothing.)
- After the last SERP: "All SERPs completed!" and back to the setup screen.

**Keyboard shortcuts.** `1` Skip, `2` Accept FB, `3` Save & Next. Ignored while typing in an input.

**Storage.** For each pyl folder:
- `<serp_id>.html`: the annotated HTML, only written when there is at least one FB. The FBs live inside it as `class="fb" data-fb-category="…" data-fb-index="…"`.
- `<pyl>.json`: the list of done SERP ids (annotated or skipped). This is how "already annotated" is decided.

### 2. GT editor (validation)

Started from Python with the parser's output (`FeatureBlock` list), the raw SERP HTML and the GT folder. There is no CLI entry point for it in `src/`.

**Compare parser output with GT** (`compare_with_ground_truth`). For each SERP, each parsed FB gets a status:

| Status | Meaning |
|---|---|
| `matched` | Same category and same normalized HTML as a GT block |
| `mismatched` | GT has this category, but the HTML differs |
| `extra` | Parser found it, GT has no block of this category left |
| `missing` | GT has it, parser did not find it |
| `extraction_failed` | Parser's XPath returned no content |
| `no_ground_truth` | No GT file for this SERP |

HTML is compared after `normalize_html`, so whitespace and similar differences don't count.

**Read-only comparison view** (`open_gt_comparison_view`). Writes temporary HTML files and opens them in the browser: a sidebar of SERPs with problems, and GT and parser output side by side, highlighted by status.

**Editable view** (`start_gt_editor`, port 5050). Same layout, plus actions per problem:

| Problem | Action | Effect |
|---|---|---|
| `mismatched` | Accept GT | Nothing saved; notes that the parser XPath must be fixed |
| `mismatched` | Accept Parsed | Moves the GT block to the element the parser's XPath finds |
| `extra` | Accept into GT | Adds the parser's block to GT |
| `missing` | Test XPath | Tries an XPath on the raw SERP; on a match, marks the problem resolved and highlights it in green |
| `extraction_failed` | — | Shows "No content extracted" |

Manual edits on the GT side: click a GT block to change its category or remove it; add a block by XPath + category; "Save Manual Edits" saves them all at once.

Every save writes a `.html.bak` backup first, renumbers `data-fb-index`, then recomputes the problems for that SERP. Problems and resolved state live in memory only and are lost when the server stops.

## Part 2: API

Neither server had a version prefix or auth. The annotator sent `Access-Control-Allow-Origin: *`. Errors were JSON `{"error": "…"}` (annotator) or `{"success": false, "message": "…"}` (GT editor).

### Annotator (`src/annotation/core/routes.py`, default port 2626)

#### `GET /serp-ids`
The current session's batch.
Response `200`:
```json
{ "serp_ids": ["…"], "total": 20, "provider": "google", "year": 2012, "language": "en" }
```
With no session: `{ "serp_ids": [] }`.

#### `GET /serp-id/{serp_id}?raw=true|false`
One SERP's HTML for the iframe, cleaned unless `raw=true`.
- `200` `text/html`
- `404` SERP id not in Elasticsearch
- `400` SERP has no `warc_location`
- `500` Elasticsearch or WARC read failed

#### `GET /get-categories?provider=…`
The feature taxonomy. `provider` only changes the `name` text; every provider gets the same list.
```json
{ "provider": "google", "name": "GOOGLE Feature Block Categories",
  "categories": [{ "id": "…", "label": "…", "description": "…" }],
  "version": "…", "last_updated": "…" }
```

#### `POST /save-annotation/{serp_id}`
Save or skip a SERP. Two body forms:
- `Content-Type: application/json` (Save): `{ "html": "<full html>", "fb_num": 2, "fbs": [{ "id": 1, "category": "…", "xpath": "…", "working_xpaths": ["…"] }] }`
- `Content-Type: text/html` (Skip): the raw HTML as body, treated as `fb_num = 0`.

Writes `<serp_id>.html` only if `fb_num > 0`; always adds the id to `<pyl>.json`. The `fbs` list is received but not stored.
- `200` `{ "success": true, "serp_id": "…", "fb_num": 2, "html_saved": true }`
- `400` no session, or empty HTML
- `500` write failed

#### `POST /test-xpath`
Test an XPath against the element marked with `fb-testing`.
Body: `{ "html": "<full html>", "xpath": "//…" }`
- `200` `{ "success": true, "match": true|false, "human_html": "…", "xpath_html": "…"|null, "message": "…" }`
- `400` missing field, no `fb-testing` element, or XPath syntax error (`success: false`)

Only the first XPath result is compared.

#### `GET /annotation`
Serves the single-page UI (`annotation.html`).

#### `GET /get-xpaths?provider_year=…&category=…` (never built)
Called by the UI to list existing XPaths for a category, expecting `{ "xpaths": [{ "expression": "…", "usage_count": 3 }] }`. No route answers it, so the dropdown always showed an error.

### GT editor (`src/validation/gt_editor_server.py`, port 5050)

| Method + path | Body | Does |
|---|---|---|
| `GET /` | — | Editor page, with entries and taxonomy embedded |
| `GET /gt/{serp_id}` | — | GT HTML, highlighted by problem status |
| `GET /ext/{serp_id}` | — | Raw SERP HTML, parser blocks and XPath-matched blocks highlighted |
| `GET /taxonomy` | — | Category list |
| `GET /problems/{serp_id}` | — | Current unresolved problems for the SERP |
| `POST /accept-parsed/{serp_id}` | `{ "category", "parser_xpath" }` | Move the GT block of that category to the parser's element |
| `POST /accept-extra/{serp_id}` | `{ "category", "parser_xpath" }` | Add the parser's element to GT |
| `POST /test-xpath/{serp_id}` | `{ "xpath", "category" }` | Test an XPath on the raw SERP against GT blocks of that category |
| `POST /save-gt/{serp_id}` | `{ "changes": [{ "action": "update"\|"remove", "fb_index", "category" }, { "action": "add", "xpath", "category" }] }` | Apply manual edits |

Problem object (returned by `/problems`):
```json
{ "feature_id": "…"|null, "serp_id": "…", "category": "…", "status": "mismatched", "xpath": "…"|null }
```

## Where each feature stands in the new app

| Old feature | Old API | New app |
|---|---|---|
| Batch of SERPs to annotate | CLI + `GET /serp-ids` | Done: `POST /carts` (pick pyl in the UI) |
| Show SERP, cleaned or raw | `GET /serp-id/{id}` | Done: `GET /serps/{id}?raw=` (snapshot cached locally) |
| Category list | `GET /get-categories` | Done: `GET /features/type` |
| Save annotation / no FBs | `POST /save-annotation/{id}` | Done: `POST /serps/{id}/annotation` (structured, not whole HTML) |
| Read an annotation back | — (open the HTML file) | Not built: `GET /serps/{id}/annotation` |
| Test an XPath | `POST /test-xpath` | Not built: `POST /xpath` (file empty) |
| Suggest existing XPaths | `GET /get-xpaths` (never built) | Not planned yet |
| LLM XPath generator | — (button only) | Not planned yet |
| Compare parser vs GT | Python function | Not built: `/validation` (open decision) |
| GT editor actions | `/accept-*`, `/save-gt`, … | Not built: "Ground-truth editing" |

See `docs/planned-features.md` for the order and open decisions.
