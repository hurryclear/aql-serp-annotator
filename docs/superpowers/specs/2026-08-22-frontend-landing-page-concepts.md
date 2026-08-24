# Landing page — concepts & rationale

Companion to [2026-08-21-cart-landing-page-design.md](./2026-08-21-cart-landing-page-design.md), which says *what* to build. This doc explains *why* it's structured that way, for someone who knows HTML/JS but has never used React. It doesn't hand you finished code — you write the actual files — but it walks through the reasoning so the shape of each file makes sense before you type it.

## 1. What we're building, and where it fits

One screen: a form (provider / year / language / your name) that, on submit, asks the backend "are there any un-annotated SERPs matching this?" and shows either "no matches" or "N ready, cart created." That's it — no navigation, no login, no annotation workspace yet (see [ADR 0005](../../adr/0005-cart-persisted-annotation-session.md) for why the whole "Cart" concept exists at all).

## 2. The React concepts this task actually needs

You don't need "all of React" — five ideas cover this entire feature.

### 2.1 Components are just functions

In vanilla JS, your unit of reuse is a function that manipulates the DOM:
```js
function renderTotal(total) {
  document.getElementById("total").textContent = total;
}
```
In React, your unit of reuse is a function that **returns a description of UI** instead of mutating the DOM directly:
```jsx
function Total({ total }) {
  return <p>{total}</p>;
}
```
That's a **component**. The weird HTML-looking syntax inside the `return` is **JSX** — it compiles down to plain JS function calls (`React.createElement(...)`), it's not a template language bolted onto JS, it *is* JS. You can drop back into `{ ... }` anywhere inside JSX to run real JS expressions (like `{total}` above).

The payoff: you stop tracking "which DOM node do I need to go find and update?" by hand. You just describe what the UI should look like *given the current data*, and React handles finding+patching the real DOM when that data changes.

### 2.2 Props: how a parent hands data to a child

`{ total }` in the function signature above is a **prop** — a plain function argument, but the caller passes it using HTML-attribute syntax: `<Total total={42} />`. Props always flow one direction: parent → child. A child can't reach up and change a prop it received; it can only ask the parent to change something (usually by calling a function the parent passed down — more on that in 2.5).

Why one-directional? Because with vanilla JS DOM manipulation, *anything* can mutate *any* element from *anywhere*, which is exactly what makes large vanilla-JS UIs hard to reason about — you can't tell by reading one function whether some other part of the code is going to reach in and change the same element later. React's rule ("data flows down, actions flow up as calls") is a constraint that keeps each component's behavior predictable from reading just that component.

### 2.3 State: data that causes a re-render

A component's local variables are useless for UI that changes over time — a normal JS variable changing value doesn't make React re-run the function and update the screen. You need `useState`:
```jsx
const [count, setCount] = useState(0);
```
`count` is the current value; `setCount` is the *only* correct way to change it. Calling `setCount(newValue)` is what tells React "re-run this component's function, something it depends on changed." This is the actual mechanism behind the declarative idea from 2.1 — state changes are the trigger, re-rendering is the response.

For our form: `App.jsx` will hold `const [result, setResult] = useState(null)`. While `result` is `null`, we're still filling out the form. Once `setResult(...)` is called with the backend's response, React re-renders `App`, and this time the condition "show the form" is false, so the confirmation view shows instead. No manual DOM swapping — you just change the data, and let the component's own logic decide what that implies for the screen.

### 2.4 Controlled inputs: keeping a `<select>`/`<input>` in sync with state

An HTML `<select>` or `<input>` normally holds its own value internally (the browser tracks it). React usually takes over that job instead: the input's `value` is driven by a state variable, and every keystroke/selection fires an `onChange` that updates that state variable. This is called a **controlled input**:
```jsx
const [provider, setProvider] = useState(PROVIDERS[0]);

<select value={provider} onChange={(e) => setProvider(e.target.value)}>
  {PROVIDERS.map((p) => <option key={p} value={p}>{p}</option>)}
</select>
```
Why bother, instead of just reading `document.querySelector(...).value` when the form submits (which would also work)? Because once the value lives in state, the rest of your component can react to it *as it changes*, not just at submit time — and more importantly, every piece of data your UI depends on lives in one consistent place (state), rather than half in state and half smeared across the DOM. For a form this small either approach would work; controlled inputs are the idiomatic React way and it's the pattern you'll see in every React codebase, so it's worth using here on purpose.

(Note the `.map(...)` above — that's how you turn the hardcoded `PROVIDERS` array from `options.js` into a list of `<option>` elements. Each item needs a `key` prop — React uses it internally to track which DOM node corresponds to which array item across re-renders. Using the value itself as the key is fine here since providers/years/languages are unique and stable.)

### 2.5 Events flow up as function calls, not as data

`SerpSelectionForm` collects the four field values, but it shouldn't decide what happens with them — that's `App.jsx`'s job (it's the one holding `result` state, and the one that will call the backend). So `App` passes a function down as a prop, and the form calls it when the user submits:
```jsx
// App.jsx
<SerpSelectionForm onSubmit={(values) => { /* call the API, then setResult(...) */ }} />

// SerpSelectionForm.jsx
function SerpSelectionForm({ onSubmit }) {
  function handleSubmit(e) {
    e.preventDefault();          // stop the browser's default full-page-reload form submit
    onSubmit({ provider, year, language, created_by });
  }
  return <form onSubmit={handleSubmit}>...</form>;
}
```
This is "lifting state up": `SerpSelectionForm` doesn't know or care what happens after submit — it just reports "the user submitted these values." `App` decides what that means (call the API, store the result). This keeps the form reusable and easy to reason about in isolation: to understand `SerpSelectionForm`, you never need to know anything about `/carts` or fetch at all.

## 3. Talking to the backend

`fetch` works exactly like you'd use it in plain JS — React doesn't change how HTTP requests work:
```js
const response = await fetch("/carts", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify(input),
});
const data = await response.json();
```
This is why `api.js` exists as its own file rather than being inlined into `App.jsx`: it's the one piece of this feature that isn't UI at all, it's "how do I talk to this backend endpoint." Isolating it means later, if the request shape changes, or you add error handling, or you write a test that fakes the network, there's exactly one place to touch — nothing about the component tree needs to know how the request is actually made.

### Why the Vite proxy, not CORS

The browser enforces the **same-origin policy**: a page served from `http://localhost:5173` (Vite) is not normally allowed to fetch from `http://localhost:8000` (FastAPI) — different port counts as a different "origin," and the browser blocks the response unless the server explicitly opts in via CORS headers. Two ways to fix that:
1. Add CORS headers to the FastAPI backend, permitting the frontend's origin.
2. Make it *look* same-origin during development: Vite's dev server proxies any request matching a path (e.g. `/carts`) to the real backend, server-to-server, where the same-origin rule doesn't apply at all.

We're using (2) — `vite.config.js`'s `server.proxy` — because it means `fetch("/carts")` in your component code never needs to know or care where the backend actually lives, and the backend doesn't need CORS middleware for what's currently a single, first-party frontend. If a second, separately-hosted consumer of this API ever shows up, that's the point to revisit and add real CORS support instead.

## 4. Why each file is shaped the way it is

| File | What it holds | Why it's separate |
|---|---|---|
| `options.js` | Plain hardcoded arrays (`PROVIDERS`, `LANGUAGES`, `YEARS`) | Pure data, no React — separating data from the component that renders it means you can change the list without touching rendering logic, and reuse it elsewhere later. |
| `api.js` | The one `fetch("/carts", ...)` call | The only non-UI, "talks to the network" code in this feature — isolating it means nothing else needs to know HTTP details. |
| `SerpSelectionForm.jsx` | Controlled inputs for the four fields + calls `onSubmit` prop | A "dumb"/presentational component — describes a form, reports what the user did, has zero opinions about what happens next. Easy to understand and test in isolation. |
| `App.jsx` | `result` state, decides what to render, calls `api.js` inside the `onSubmit` handler | The "smart"/container component — the one place that coordinates state and the API call. Everything else is a pure function of `result`. |
| `vite.config.js` | `server.proxy` entry | Dev-only routing concern, unrelated to any component — belongs in build tooling config, not component code. |

This split — dumb form component vs. smart container component holding state — is one of the most common patterns you'll see in real React codebases, so it's worth internalizing here on a small, low-stakes example before you meet it in something bigger.

## 5. What you'll actually write, in order

1. `options.js` — plain arrays, no new concepts.
2. `api.js` — a `fetch` wrapper; concepts: async/await (you may already know this).
3. `SerpSelectionForm.jsx` — concepts: JSX, controlled inputs, the `onSubmit` prop pattern from 2.5.
4. `App.jsx` — concepts: `useState`, conditional rendering, calling `api.js` from an event handler.
5. `vite.config.js` proxy entry — no React concepts, just config.

Each step, I'll explain what that specific file needs to accomplish and which concept above it exercises; you write it, I review.