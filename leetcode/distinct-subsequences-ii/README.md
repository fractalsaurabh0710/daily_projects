# Distinct Subsequences II (LeetCode 940)

Count the distinct non-empty subsequences of a string, modulo 1e9+7.

## Run

    python3 solution.py

Runs the tests, then prints a small table and a trace.

## The idea

Counting subsequences is trivial — there are `2**n - 1` non-empty ones. The word
*distinct* is the whole problem: once characters repeat, different index sets
spell the same string, and any counter that tracks index sets double-counts.

So count by **last character** instead. With `end[c]` the number of distinct
subsequences ending in `c`, reading a character `x` gives

    end[x] = 1 + sum(end.values())

appending `x` to every distinct subsequence so far, plus `x` alone. The point is
that this **overwrites** `end[x]` rather than adding to it: every subsequence
that used to end in `x` is also reachable by swapping in this later `x`, so the
old set is a subset of the new one. The overwrite *is* the deduplication.

Two forms are implemented — the dict version that re-sums each step
(O(n·alphabet)), and one that carries the running total, where the overwrite
becomes `total = 2 * total + 1 - end[x]` in O(n).

## Tests

Brute force materialises the actual set of subsequences, and both
implementations are checked against it on all 8190 strings of length ≤ 12 over
`{a, b}` — the densest possible repeat structure — plus 300 random strings over
`{a, b, c}`, the LeetCode examples, and `2**n - 1` for all-unique inputs.
