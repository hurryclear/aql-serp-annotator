# Parser development: design

Status: approved in chat, 2026-11-10 (revised the same day: one SERP at a time, reuse first)
Branch: `claude/parser-development` (stacked on `claude/annotation-editor`; a reference implementation, not merged into main)

## Why

After annotating and reviewing, the annotated SERPs are used to find **parsers**: one xpath that finds a feature type's blocks. This step only **finds, tries and links** parsers; running them over AQL and validating come later.

Pipeline: annotate → edit/confirm (editor) → **parser development** → (later) parsing and validation.

The parser table works as a **library**: for each SERP the first question is whether a known parser already works on it, and only if none does is a new one written.

## Screens

### Start: the editor's group table (`/editor`)

Each provider + year group has a **Design parsers** button next to Open.

### Design page (`/parsers/:providerId/:year`)

Same layout as the annotation page and the editor; Previous / Next go through the group's SERPs.

- **Left:** the annotated SERP with its blocks highlighted (green, labelled by type). Elements an xpath finds get a blue ring.
- **Right:** one section per feature type annotated **on this SERP**:
  - this SERP's blocks of the type, and which parser each is linked to now
  - one searchable box: type a new xpath, or pick an **existing parser of the same provider and feature type, of any year**
  - **Parse this SERP**: found / missed / extra for this SERP
  - **Use this parser** (an existing parser was picked): link it to this SERP's blocks it finds
  - **Save as new parser** (the text is a new xpath): save it and link this SERP's blocks it finds
  - delete a picked parser

## Rules

- Everything happens on **one SERP**: trying, saving and using only touch the current SERP's blocks.
- A parser must find at least one annotated block of its type on the SERP to be saved or used (422 otherwise).
- **Links:** `feature.parser_id`. A block holds one link; using another parser on it replaces the old one. Deleting a parser removes all its links.
- **No in-place editing.** A parser can be linked to SERPs of several years, so changing its xpath would silently change what it finds there. Picking a parser and changing its text makes a new parser on save.
- **Id:** deterministic, `uuid5(NAMESPACE_FEATURE_PARSER, "provider:year:feature_type:k")`, with the year of the SERP it was designed on and k = 1, 2, …; the year only makes the id unique.
- **No names for now:** `created_by` is stored empty; the column stays for later.
- "Found" is decided by element numbers (`aqlqa-node`): an annotated block is found when the xpath returns that very element. Only element results count. An invalid xpath answers 422 with lxml's message.

## Routes

| Route | Does |
|---|---|
| `POST /parsers/try` | run an xpath on one SERP: found / missed / extra |
| `GET /parsers?provider_id=…&feature_type=…` | a provider's parsers of every year (type optional), with how many SERPs and which years they're linked to |
| `POST /parsers` | save a new parser from one SERP and link its blocks there |
| `PUT /parsers/{id}/serps/{serp_id}` | use an existing parser on a SERP (link its blocks there) |
| `DELETE /parsers/{id}` | unlink everywhere and delete |

## Out of scope

- Running parsers over AQL, producing output, validation.
- An LLM xpath helper.
- Parsers made of several xpaths (one parser = one xpath).
