# Frontend scaffolding guide

A step-by-step checklist for (re)creating `frontend/` as a Vite + React + TypeScript app. Written so you can follow it yourself later without needing this conversation's context. For *why* each React/TS concept works the way it does, see the companion doc: [2026-08-22-frontend-landing-page-concepts.md](../superpowers/specs/2026-08-22-frontend-landing-page-concepts.md).

Decisions this guide assumes (see chat history / commit messages for the reasoning, or ask to have it added to an ADR):
- **React**, not Angular — [ADR 0001](../adr/0001-fastapi-react-monorepo.md).
- **TypeScript**, not plain JS — undocumented at the ADR level as of this writing; add a note to ADR 0001 if you want it recorded there.
- **No meta-framework** (no Next.js) — this app has its own FastAPI backend doing all data/business logic already, and no current need for server-rendering or multiple real URLs. Revisit only if that changes.
- **No frontend router yet** (no React Router) — the app currently has at most two screens (landing form, later an annotation workspace), handled via plain conditional rendering on a state value, not real distinct URLs. Add React Router if/when a screen needs its own bookmarkable/shareable URL.

## 1. Rescaffold with Vite's official `react-ts` template

Checked before doing this: `frontend/` was confirmed untracked in git and unmodified from the stock Vite template (only `typescript` had been added to `package.json` via `npm install -D typescript`, which the fresh template includes anyway) — so nothing is lost by regenerating it.

From the repo root:
```
npm create vite@latest frontend -- --template react-ts
```
The CLI will ask to confirm clearing the existing `frontend/` directory since it's non-empty — safe to confirm, per the check above. Then:
```
cd frontend
npm install
```

**Verify what you got** — the template should include, beyond the plain-JS scaffold:
- `tsconfig.json` (root — just references, no real compiler options)
- `tsconfig.app.json` (real config for `src/`)
- `tsconfig.node.json` (real config for `vite.config.ts`)
- `src/main.tsx`, `src/App.tsx` (not `.jsx`)
- `vite.config.ts` (not `.js`)
- `eslint.config.js` referencing `typescript-eslint`
- `package.json` build script as `tsc -b && vite build` (type-checks before building, since Vite/esbuild itself doesn't check types)

If any of these don't match, something about the template version has changed since this guide was written — read the generated file directly rather than assuming this list is still accurate.

## 2. Read through `tsconfig.app.json` against this checklist

Confirm (or adjust) these options are present, and that you understand *why* each is there — see the concepts doc's tsconfig section for the full reasoning:
- `"target"`: a modern ES version (e.g. `"ES2022"`)
- `"lib"`: includes `"DOM"` and `"DOM.Iterable"` — without this, TypeScript doesn't know what `document`/`window` are
- `"module"`: `"ESNext"`, `"moduleResolution"`: `"Bundler"` — defers actual module resolution to Vite
- `"jsx"`: `"react-jsx"` — modern JSX transform, no manual `import React` needed per file
- `"strict"`: `true`
- `"noEmit"`: `true` — this config only type-checks; Vite/esbuild produces the actual JS
- `"include"`: `["src"]`

## 3. Add the dev-proxy config

`vite.config.ts` needs a `server.proxy` entry so `fetch("/carts")` in the browser (served from Vite on port 5173) reaches the FastAPI backend (port 8000) without a CORS error — see the concepts doc's "Why the Vite proxy, not CORS" section for the reasoning.
```ts
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/carts": "http://localhost:8000",
    },
  },
})
```
Add more path entries here as more routes get built (`/serps`, `/xpath`, `/features`, per the backend spec's router list).

## 4. Build the feature files

Once the scaffold + proxy are in place, write these in order (each one covered concept-by-concept in the companion doc):
1. `src/options.ts` — hardcoded `PROVIDERS`/`LANGUAGES`/`YEARS` arrays.
2. `src/api.ts` — the `fetch("/carts", ...)` wrapper.
3. `src/SerpSelectionForm.tsx` — the form component.
4. `src/App.tsx` — state + conditional rendering + wiring the form to the API call.

## 5. Sanity-check before moving on

- `npm run dev` in `frontend/`, `uvicorn` (or however the backend's run) in `backend/`, both running side by side.
- Open the Vite dev URL, fill the form, submit, and confirm in the Network tab that the request actually reaches the FastAPI backend (not a 404 from Vite's own dev server) and the response shape matches `CartOutput`.