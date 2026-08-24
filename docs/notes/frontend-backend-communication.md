# Roundtrip

## The core idea

Your React app (running in the browser) and the FastAPI backend (backend/app/main.py) are two completely separate running programs. They don't share memory, and you can't just call a Python function from JS.
- The only way they communicate is **by sending messages over the network using HTTP** — the same protocol your browser uses to load any web page, just used here to move data instead of HTML pages.

## HTTP
What makes it a "POST" specifically: HTTP defines a handful of "methods" that signal intent:
- `GET` — "give me data" (no body, just asking to read something)
- `POST` — "here's some data, do something with it / create something new"
- (there are others — PUT, DELETE, etc. — not relevant here)

Look at backend/app/routers/carts.py:10 — @router.post("/carts"). FastAPI registers that function as the handler for "any POST request that
arrives at the path /carts." So when your frontend calls apiClient.post("/carts", input), you're not calling that Python function directly
— you're sending a real network message that says "POST request, path /carts," and it's the backend's routing (matching method + path,
like a switchboard) that decides this function should handle it.

## What's actually inside the request (from frontend), two parts:

- **Headers**: metadata about the request (axios sets Content-Type: application/json automatically, telling the backend "the body is JSON")
- **Body**: the actual payload. input (your CartInput object) gets converted to a JSON string by axios and sent as this body: {"provider": "...", "language": "...", "year": 2023, "created_by": "...", "batch_size": 25}

## What happens on the backend

- FastAPI receives that raw HTTP request, sees the cart_input: CartInput parameter on the create function
- and automatically parses the JSON body into a CartInput instance for you (this is FastAPI's big feature — the same thing axios does for you on the way out, FastAPI does on the way in).
- It runs create_cart(cart_input=cart_input), gets a CartOutput back, and serializes that to JSON as the HTTP response body.

## What comes back to you

- an HTTP response — a status code (like 200, meaning success) plus a JSON body containing the CartOutput data. axios receives this, automatically parses the JSON, and hands you back that response object — which is why the next line of our function needs to reach into response to find where axios put that parsed body.

## So the whole round trip is

JS object → JSON text → network → FastAPI parses JSON back into Python → Python object → JSON text → network → axios parses JSON back into a JS object. Nothing is shared directly; everything crosses that boundary as JSON text.
