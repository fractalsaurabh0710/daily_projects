# Algebraic Effects

Algebraic effects in ~80 lines of generators: a program says *what* it wants with
`yield perform('fetchUser', id)` and a stack of handlers decides *how*.

```
node effects.js
```

Zero dependencies, Node 18+.

## The idea

A generator yielding an effect is suspended, not finished. A handler computes a
value and that value is passed *back in*, so the generator resumes at the exact
expression that asked. This is the one thing `try`/`catch` cannot do: a catch
block runs after the stack between it and the failure is already gone, so there
is nowhere left to resume to.

`handle(handlers, genFn)` returns another generator function rather than running
anything. That is what makes layers compose:

- an effect a layer does not recognise is re-yielded outward untouched, and the
  answer from the outer layer is threaded back in;
- a handler may itself `perform` effects, which belong to the layers outside it;
- nothing in either the program or the handlers knows whether the whole thing is
  synchronous or asynchronous. That is decided by the runner at the very top —
  `run` awaits promises a handler bubbled up, `runSync` refuses to, which turns
  "this program does no I/O" into something a test can assert.

## What the five checks show

The same untouched `loadReport` generator runs under a plain lookup table and
under an `async` fetcher with a `setTimeout` in it, and produces identical output
and identical logs. Then a nested pair of layers, where the inner `log` handler
performs `now` and the outer one answers it. Then the resumption case: an inner
layer re-performs `fetchUser` outward, the outer flaky one throws, the throw
lands at that `yield`, and the handler hands back a placeholder user — so the
loop continues to the next id rather than unwinding. Finally, an effect nobody
handles surfaces as a named `Unhandled` error instead of a silent hang.
