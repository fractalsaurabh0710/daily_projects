# Russian Doll Envelopes

LeetCode 354. Each envelope is `(width, height)`, and one fits inside another
only if **both** dimensions are strictly smaller. Find the longest nesting
chain.

```
python3 solution.py
```

Runs its own tests: the LeetCode examples, degenerate shapes, a 50-long chain,
a 50-element antichain, and 400 random cases cross-checked against an
independent O(n²) oracle — with coordinates drawn from 1–8 so ties are the
common case rather than a corner. Then one 100,000-envelope run to show the
fast path is actually fast.

## The interesting part

Sort by width and the problem collapses to longest increasing subsequence over
the heights — except that sorting by width does not separate envelopes that
*share* a width, and those can never nest. Sorted `(3,1) (3,2) (3,5)`, the LIS
pass happily takes all three and reports a chain of 3 where the answer is 1.

Sorting the heights **descending** inside each width fixes it for free: a tied
group is then strictly decreasing, so no increasing subsequence can take two of
its members. The comparison the algorithm cannot make is pushed into the
ordering instead. `max_envelopes_ascending_tiebreak` is the buggy variant, kept
so a test can show the difference rather than a comment claiming it.

The O(n²) oracle has its own trap: "fits inside" is a partial order, not the
array order, so a plain left-to-right pass reads entries it has not settled
yet. It is written as memoized recursion for that reason.
