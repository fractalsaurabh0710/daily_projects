# Call-Tree Profiler

A deterministic profiler in ~170 lines of standard library, built on
`sys.setprofile`. Where `cProfile` prints a flat table — one row per function,
all its callers smeared together — this keeps the *shape* of the run: who called
whom, and how much time went down each distinct path. The output is an indented
tree with cumulative time, self time, call counts and percentage bars.

## Run it

    python3 profiler.py

That runs a self-test (it rebuilds the 177 calls and depth-10 shape of `fib(10)`
by hand and asserts the tree matches), then profiles a small demo workload —
recursive fib, a list comprehension, and some dict churn — and prints the tree.

Use it on your own code as a context manager:

```python
with CallTreeProfiler() as p:
    your_code()
p.report(min_pct=1.0, max_depth=5)
```

## Notes

`sys.setprofile` fires on `call`/`return` for Python frames and `c_call`/`c_return`
for builtins, which is why `builtins.sorted [C]` shows up as its own node — a
flat table usually hides that. CPython disables the profile hook while the hook
itself is running, so the hook's own cost is the only skew, and it's charged to
whichever frame was active.

Two things worth knowing about the numbers. Recursive paths double-count
cumulative time by construction: each `fib` level reports the whole subtree below
it, so the column does not sum down the tree. And the frame that calls `__exit__`
never receives its `return` event, so the profiler closes any frames still on the
stack itself using the exit timestamp.
