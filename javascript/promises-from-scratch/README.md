# Promises from Scratch

A `Promise` implementation built on `queueMicrotask` and nothing else, written to
match the native one *tick for tick* rather than merely "call the callback later".

## Run

```
node test.js
```

The test runs one identical program against `Promise` and against `TinyPromise`
and prints the two logs side by side. They come out line for line identical:

```
native            | tiny
------------------+------------------
1 a                | 1 a
1 b                | 1 b
...
2 adopted inner    | 2 adopted inner
```

## The interesting part

Callback *order* is the whole specification. Getting the right value to the right
handler is easy; landing on the same microtask tick as V8 is where the spec earns
its length. Three places cost a tick that you might not expect:

- `.then()` on an **already settled** promise still defers one tick. It never
  calls back synchronously.
- A `.then()` with **no handler** for the path taken (`.then(onFulfilled)` on a
  rejection) still costs a tick to pass the value through.
- **Returning a promise** from a handler costs **two** — one to queue the
  adoption job, one more inside that promise's own `.then()` to schedule its
  reaction. That is why `2 adopted inner` finishes last in the test output,
  behind handlers that were registered after it.

The other subtlety is that resolve-once and settled-ness are two different
flags. `resolve(somePromise)` locks the promise against further resolution
immediately, but it stays pending for at least two more ticks while the thenable
is adopted — so a single `state` field cannot carry both facts.
