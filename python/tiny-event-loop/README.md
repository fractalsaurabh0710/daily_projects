# Tiny Event Loop

A cooperative event loop in one file — `async`/`await` concurrency without
`asyncio`, built from generators, a heap, and a virtual clock.

A task is a generator that yields a request to the scheduler. Four requests
cover the useful cases:

| Yield | Resumed |
| --- | --- |
| `None` | on the next turn (round-robin) |
| `Sleep(seconds)` | once the clock reaches `now + seconds` |
| `Spawn(gen)` | immediately, with the new `Task` handle |
| `Join(task)` | once `task` finishes, with its return value |

`gather(*coros)` is written in terms of those: spawn everything, then join
everything, returning results in argument order regardless of who finished first.

## Run

    python3 loop.py

The six assertions at the bottom are the whole test suite — concurrency timing,
round-robin order, joining an already-finished task, two tasks waiting on one
result, and a bad yield raising instead of hanging.

## The interesting part

The clock is virtual. `Sleep` does not sleep; it reschedules the task at
`now + seconds`, and the loop jumps the clock straight to the next deadline
whenever the ready heap is drained. So concurrency is *measurable*: three jobs
sleeping 1, 2 and 3 seconds finish at virtual time 3, not 6, and the test
asserts that number exactly — in a run that takes microseconds and gives the
same timings every time. The `_seq` counter in the heap entries is what keeps
same-deadline tasks strictly FIFO, which is the only reason those orderings are
deterministic enough to assert on.
