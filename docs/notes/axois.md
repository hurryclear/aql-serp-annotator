# `apiClient.post("/carts", input)` 

Good follow-up — I described the HTTP round trip in the abstract; axios is the concrete tool actually *doing* that round trip on the JS side.

**Without any library**, the browser gives you a built-in function called `fetch()` to do this manually. It would look something like:

```typescript
const res = await fetch("http://localhost:8000/carts", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(input),
});
const data = await res.json();
```

Notice everything you have to do by hand: pick the method, set the header yourself, `JSON.stringify` the body yourself, and then separately call `.json()` to parse the response body back into an object — and if the backend returns an error status (like 404 or 500), `fetch` *doesn't even throw* — it just resolves normally, and you have to check `res.ok` yourself.

**What axios does is remove all of that boilerplate.** 

Concretely, in `apiClient.post("/carts", input)`:
1. It builds the actual network request (still ultimately using the browser's networking underneath, but you never see that layer)
2. It automatically `JSON.stringify`s `input` and sets the `Content-Type` header — you just pass a plain JS object
3. It merges `"/carts"` with the `baseURL` you configured in `client.ts`
4. It returns a `Promise` that resolves once the response arrives
5. It automatically parses the JSON response body back into a JS object for you (that's the `response.data` we're about to use — with raw `fetch` you'd have had to call `.json()` yourself)
6. If the backend responds with an error status code, axios automatically makes the `Promise` reject (throw), instead of silently returning success like raw `fetch` does — so error handling later is a normal `try/catch`

So axios isn't doing anything *fundamentally* different from what raw `fetch` can do — it's the same HTTP mechanism underneath — it's just packaging the common, repetitive parts (JSON in/out, base URL, error behavior) into a nicer API so you don't rewrite that boilerplate every time you call the backend.
