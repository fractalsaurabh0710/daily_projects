# Fractional Cascading

Find a query's successor in each of *k* sorted lists with **one** binary search
instead of *k* of them: `log n + O(k)` comparisons rather than `k log n`.

Every second element of each list is promoted into the list above it, carrying a
*bridge* back to where it came from. The single binary search lands in the top
augmented list; after that each level is a pointer hop plus a short scan, and the
promoted elements are dense enough that the scan is never longer than two steps.

## Run

    python3 main.py

No dependencies. It checks itself against `bisect` on 40 random structures
(126 queries each), then counts comparisons against the naive k-binary-searches
baseline:

```
  k      n   naive cmp/query   cascaded   speedup   max scan steps
  16    256           128.1        46.4      2.76x               2
  16  16384           224.0        52.5      4.27x               2
  64    256           512.6       166.0      3.09x               2
  64   4096           768.0       170.4      4.51x               2
```

The gap widens with `n` and narrows with `k`, exactly as `k log n` vs
`log 2n + 2k` predicts. Augmented space measured at 1.95x the input, the
geometric series `n(1 + 1/2 + 1/4 + ...)`.

## The one thing that is easy to get wrong

The bridge has to point at the last promoted entry *strictly before* the query
position, not at the first one at or after it. An entry sitting exactly at the
query position already has value `>= q`, so its source in the list below sits at
or past the answer — start there and the scan, which only moves forward, walks
away from the successor and reports the wrong one. Bridging strictly backwards
keeps the start point below the answer, and the two-step bound is what makes
that safe: if two consecutive positions below the answer were both skipped, one
of them would have been promoted (promotion takes every other element), which
would have given a later bridge than the one taken.
