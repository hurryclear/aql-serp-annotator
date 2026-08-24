# Promise

- Promise: an object in JavaScript, that represents a value that doesn't exit yet, but will - or an error, if something goes wrong.
- Three states:
    - pending — the operation hasn't finished yet
    - fulfilled — it succeeded, and now holds a value
    - rejected — it failed, and now holds an error

No — `Promise` is a plain **JavaScript** feature (part of the language itself, available in any browser or Node, no TypeScript needed). It's been in JS since ES2015, well before TypeScript was widely used.

What TypeScript adds on top is purely a _type-level_ annotation: `Promise<CartOutput>` lets you say "this isn't just any Promise, it's specifically a Promise that, once fulfilled, will contain a `CartOutput`." That generic parameter (`<CartOutput>`) is a TS-only concept for describing _what's inside_ — but the `Promise` mechanism itself, and `async`/`await`, are runtime JavaScript behavior that exists independent of TypeScript entirely.

This is the same split as the `number` question earlier: JS has a real thing (numbers at runtime, Promises at runtime), and TypeScript's job is to describe those real things more precisely at compile time, not invent new runtime behavior.

# 