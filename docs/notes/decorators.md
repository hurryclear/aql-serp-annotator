# Understanding decorators, and `@dataclass`

This note explains what a decorator actually is, then walks through `@dataclass`, using `backend/schemas.py`'s `AnnotatedFeatureInput`/`AnnotatedFeatureOutput` as the concrete example. If you've already read [fastapi-lifespan.md](fastapi-lifespan.md), you've seen one decorator (`@asynccontextmanager`) in passing — this note is the general concept, with a second concrete example.

## What a decorator actually is

A decorator is a function that wraps another function or class, adding behavior to it without you having to modify its insides. Analogy: think of it as a gift wrapper around a box. The box's contents (your function/class body) stay exactly what you wrote — the wrapper just adds something extra that happens whenever someone interacts with the box.

The `@` syntax is shorthand. Writing:

```python
@some_decorator
class Foo:
    ...
```

is exactly equivalent to:

```python
class Foo:
    ...

Foo = some_decorator(Foo)
```

That's it — a decorator is just a function that takes your class (or function), does something with/to it, and returns a (possibly modified) result, which then replaces the original name. The `@` line is purely a shorter way to write that second line's transformation.

You've already seen two different decorators doing two very different things with that same mechanism:
- `@cached_property` (in `config.py`) — turns a method into something accessed like a plain attribute, cached after first access.
- `@asynccontextmanager` (in `main.py`) — turns a generator function into something usable as an async context manager.

`@dataclass` is a third example, doing yet another kind of transformation.

## What `@dataclass` specifically does

Take your own code, `backend/schemas.py`:

```python
from dataclasses import dataclass

@dataclass
class AnnotatedFeatureInput:
    type: str
    content: str
    xpath: str
```

Without `@dataclass`, a plain class with just those three lines would do almost nothing useful — Python wouldn't know how to build one from arguments, print it usefully, or compare two instances for equality. You'd have to hand-write all of that yourself:

```python
class AnnotatedFeatureInput:
    def __init__(self, type: str, content: str, xpath: str):
        self.type = type
        self.content = content
        self.xpath = xpath

    def __repr__(self) -> str:
        return f"AnnotatedFeatureInput(type={self.type!r}, content={self.content!r}, xpath={self.xpath!r})"

    def __eq__(self, other) -> bool:
        if not isinstance(other, AnnotatedFeatureInput):
            return NotImplemented
        return (self.type, self.content, self.xpath) == (other.type, other.content, other.xpath)
```

`@dataclass` generates all of that boilerplate for you, automatically, from just the field annotations (`type: str`, `content: str`, `xpath: str`). Specifically, it looks at your class body, sees these look like field declarations (a name plus a type, no method), and builds:

- `__init__` — so `AnnotatedFeatureInput(type="answer_box", content="<div>...</div>", xpath="//div[@id='x']")` works, positionally or by keyword.
- `__repr__` — so printing an instance shows its actual field values instead of Python's default unhelpful `<AnnotatedFeatureInput object at 0x...>`.
- `__eq__` — so two instances with the same field values compare equal (`==`), instead of Python's default (compare by object identity — always `False` for two separately-constructed instances, even with identical data).

## Why this fits DTOs specifically

A DTO (like `AnnotatedFeatureInput`/`AnnotatedFeatureOutput`) is, by definition, a class whose entire job is holding a fixed set of named values — no custom methods, no internal logic, just data crossing a boundary. That's exactly the case `@dataclass` is built for: it assumes "this class is just data" and generates precisely the boilerplate that assumption implies. If a class needed custom behavior beyond that (validation, computed properties, etc.), you'd reach for something more — but for a pure data container, `@dataclass` is the whole solution in three lines.

## One naming note, unrelated to decorators

`class AnnotatedFeatureInput ():` (with a space and empty parentheses) works, but is unnecessary — `class AnnotatedFeatureInput:` means exactly the same thing. Empty parentheses only matter when you're actually inheriting from something (e.g. `class Foo(Base):`); with nothing to inherit from, they're just noise.
