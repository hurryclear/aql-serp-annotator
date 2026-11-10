# Annotation editor: design

Status: approved in chat (mockup), 2026-11-10
Branch: `claude/annotation-editor` (stacked on `claude/annotation-feature-ef421f`; a reference implementation, not merged into main)

## Why

After a first round of annotation, annotations need to be reviewed, corrected and confirmed. Viewing and editing are one tool, because you always review before you change anything. It is called the **editor**.

## Screens

### Editor home (`/editor`)

- Loads a summary from the database as soon as it opens.
- Groups annotations by **provider and year** only (no language split), ordered by provider, then year.
- Per group: the number of annotations ("Annotation") and how many are ground truth. (A "with / without features" split was tried and dropped, 2026-11-10.)
- Each group has an "Open" button.

### Editor workspace (`/editor/:provider/:year`)

Same layout and style as the annotation page.

- **Top bar:** "SERP n of N", the SERP id, provider and year, Previous / Next, Back to groups.
- **Left:** the annotated SERP with its blocks highlighted (green, as accepted blocks on the annotation page) and a small type label on each block.
- **Right panel:**
  - the SERP's features: change a feature's type (dropdown) or delete it (✕)
  - add a feature: mark in DevTools (`aqlqa-sf-testing`), choose a category, Add (same steps as annotating)
  - **Save changes**
  - **Confirm as ground truth** (sets `ground_truth` = 1); on a confirmed annotation the same button reads **Unconfirm ground truth** (sets it back to 0). Confirming needs saved changes first; unconfirming always works.

## Rules

- **Saving replaces the whole feature list** (PUT). Ids are recomputed in page order, so blocks that didn't move keep their ids.
- A block that still exists after an edit **keeps its `parser_id`**.
- **Any edit resets `ground_truth` to 0**; only "Confirm as ground truth" sets it to 1.
- The snapshot's marks are rewritten on save: old `aqlqa-sf-type` attributes are removed, new ones written. `aqlqa-node` numbers never change.
- Saving an empty list is allowed and means "No features".

## Routes

| Route | Does |
|---|---|
| `GET /annotations/groups` | provider + year groups with counts |
| `GET /annotations?provider_id=…&year=…` | the group's annotated SERPs |
| `GET /annotations/{serp_id}` | one annotation and its features (with each feature's element number) |
| `PUT /annotations/{serp_id}` | replace the feature list |
| `PATCH /annotations/{serp_id}` | `{"ground_truth": true}` confirms it |

## Out of scope

- Deleting a whole annotation.
- Recording who edited (the table has only `created_by`).
- A separate visual design; the editor reuses the annotation page's style.
