# Landing page and annotation page: design

Status: draft, ready for review
Date: 2026-10-29

## Why

The React frontend has a working landing page form but the annotation workspace is a stub (`AnnotationPage` says "coming soon"). This doc fixes what both pages look like and how the annotation page behaves, so the workspace can be built without going back to the user for layout decisions.

The old Flask page (`src/annotation/frontend/annotation.html`) is the reference for the workflow. The new pages keep its flow and drop the parts that were already switched off.

## Goals

- An annotator can open a cart, go through its SERPs one by one, mark every feature block on each, give each block a category, and save.
- Both pages look like one app: same component library, same colours, same card style.
- Marking a block stays exact: the annotator chooses the precise DOM node.

## Non-goals (for now)

- XPath tools: no XPath input, no tester, no "existing XPaths" list, no AI XPath generator.
- Clicking an element on the SERP to mark it. Clicking lands on the wrong (usually too small) node; the annotator needs the exact node, which DevTools gives.
- Resuming an unfinished cart (ADR 0005 leaves this out).
- Login or user accounts. The annotator name stays free text.

## Anti-goals

- Saving a block that isn't the node the annotator meant. Anything that guesses the node is worse than the manual DevTools step.
- Losing accepted blocks without telling the annotator (for example, a failed save that looks like it worked).

## Shared style (both pages)

- Build both pages with MUI, which `LandingPage` already uses. Put one MUI theme in one file and wrap the app in it, so colours, font and corner radius are set once. *(Builder's call: file name and exact theme values.)*
- Light grey page background. Content sits on white cards with a thin border and rounded corners.
- One blue (primary) button per page: "Start annotating" on the landing page and "Save and next" on the annotation page. Every other button is outlined.
- Error messages appear inline in red text next to what they're about. No `alert()` popups.
- Labels use sentence case ("Save and next", not "Save And Next").

## Landing page (`/`)

Approved mockup: a single centred card, about 380px wide.

- Title "AQL SERP annotation", with one line under it: "Choose which SERPs to annotate in this sitting."
- Four fields, all required: Provider, Language, Year (dropdowns), and Your name (text).
- A hint line: "You'll get up to 25 SERPs you haven't annotated yet."
- Full-width blue "Start annotating" button.
- If any field is empty, the button doesn't submit and the empty fields are highlighted as errors.
- If the backend returns `id: null`, show "No SERPs match these choices. Try a different year." in red under the button.
- If the request fails, show a red inline error under the button too.
- On success, go to `/workspace/{cartId}`.

The dropdown option lists stay hardcoded for now. Moving them to a backend route is a separate planned item ("One source of truth for providers, languages and years" in `docs/planned-features.md`).

## Annotation page (`/workspace/:cartId`)

Approved mockup: a top bar across the full width, then the SERP on the left (takes the remaining width) and a step panel on the right (about 300–480px wide). It keeps the old page's split. The layout may change later.

### Top bar

- "SERP 3 of 25", a thin progress bar, and the cart's provider, language and year.
- An "Exit" button that goes back to the landing page. SERPs that weren't saved aren't lost: they can come up in a later cart, because only SERPs that have an annotation are excluded.

### SERP area

- Shows the current SERP's HTML from `GET /serps/{id}` inside an iframe.
- A block the annotator has marked (class `fb-testing`) gets an orange outline. Blocks already accepted on this SERP get a different, quieter outline. *(Builder's call: the exact styles, injected into the iframe.)*

### Step panel

Heading: "Feature block #N", where N is the number of the block being annotated on this SERP.

1. **Mark it in DevTools.** Shows the command `$0.classList.add('fb-testing')` with a copy button.
2. **Choose a category.** A grid of buttons, two per row, one per feature type. The selected button is highlighted. If the list is long the panel scrolls.
3. **"Accept block"** (shortcut `2`). Finds the element with class `fb-testing` in the iframe, records it with the chosen category, swaps its class to the "accepted" style, clears the category choice, and moves to block N+1.
   - If no element is marked, or no category is chosen, show a red inline message in the panel and accept nothing.
4. **"Accepted on this SERP (count)".** A list: "#1 Top stories", and so on. Each row has an × that removes that block (and removes its outline in the iframe).
5. At the bottom of the panel:
   - **"Save and next"** (blue, shortcut `3`): saves all accepted blocks for this SERP, then loads the next SERP. If no block is accepted, it shows a red message pointing to "No blocks" instead of saving.
   - **"No blocks"** (outlined, shortcut `4`): saves an empty annotation. The SERP counts as done and is never offered again. If blocks are already accepted, ask for confirmation first, because they would be thrown away. *(My call: the confirmation and the `4` key.)*
   - **"Skip"** (outlined, shortcut `1`): saves nothing and loads the next SERP. The SERP can come up again in a later cart. Use it when a SERP won't load or you're unsure.

The keyboard shortcuts must not fire while the focus is in a text field.

### After the last SERP

Show a simple "All 25 done" card (same card style as the landing page) with a button back to the landing page.

### Errors

- The SERP fails to load: show a red message in the SERP area. "Skip" stays usable so the annotator isn't stuck.
- A save fails: show a red message in the panel, keep the accepted blocks, and stay on the current SERP so the annotator can retry.
- The save returns "already annotated" (`AnnotationExistsError`, planned as 409): show a message and move on to the next SERP. *(My call: the ADR 0005 filter should prevent this, so it's rare. Overwriting is out of scope here.)*

## Constraints the builder must handle

- **The iframe must be readable from the React page.** Accept has to find `.fb-testing` inside it. The frontend runs on `localhost:5173` and the backend on `:8000`, so an iframe with `src` pointing at the backend is cross-origin and its document can't be read. Fetch the HTML with axios and put it into the iframe with `srcdoc` (without a `sandbox` attribute that blocks same-origin access). The old Flask page didn't have this problem because it served both from one origin.
- **The `serp_ids` must reach the annotation page.** `LandingPage` gets them from `POST /carts` but `navigate()` drops them today. Pass them with router state (`navigate(url, { state })`). A page refresh loses them; ADR 0005 accepts that. If they're missing, show a message with a link back to the landing page.
- **Backend routes that don't exist yet** (from `docs/planned-features.md`):
  - `GET /features/type`: the category list (item 1).
  - `POST /serps/{id}/annotation`: the save (item 3). It takes `cart_id` and a list of `{type, content, xpath}` (`AnnotatedFeatureInput`).
  - `GET /serps/{id}` already exists.
- **What a saved block contains:** `type` is the chosen category, and `content` is the marked element's `outerHTML` with the annotation classes (`fb-testing`, `fb-accepted`) removed. *(My call.)* `xpath` is sent as `null`.
- **`xpath` becomes optional in the backend.** Change `xpath: str` to `xpath: str | None` in `AnnotatedFeatureInput` and `AnnotatedFeatureOutput` (`backend/schemas.py`) and in `AnnotatedFeature` (`backend/persistence/models.py`). `Base.metadata.create_all` doesn't change tables that already exist, so a SQLite file created before this change keeps `xpath NOT NULL`. Delete or recreate the local test database. Check whether any prod database exists before shipping.

## Left to the builder

- The component breakdown (for example `TopBar`, `SerpFrame`, `StepPanel`, `CategoryGrid`, `AcceptedList`) and where state lives.
- The theme file and its values, within the shared style above.
- How the outline styles are injected into the iframe.

## Changes to other docs

`docs/planned-features.md` item 6 currently says "click to select a block, test its xpath". This design replaces that with DevTools marking and no XPath step; update item 6 to point here.

## Decided

- "Skip" and "No blocks" are two separate buttons (user, 2026-10-29). This matches `docs/planned-features.md` item 6 and differs from the old page, where Skip saved an empty annotation.
- `xpath` is optional and stored as `NULL` for now (user, 2026-10-29). Known cost: the old tool kept each block's position by saving the whole SERP HTML with `class="fb"` on each block. The new backend stores only the block's own HTML, so where the block sat on the page is not recorded. Computing the exact path automatically was considered and set aside.
