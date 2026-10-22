# Burst Balloons (LeetCode 312)

Balloons in a row carry numbers. Bursting balloon `i` pays
`left * nums[i] * right`, where `left` and `right` are its *current* neighbours —
the row closes up behind every balloon already burst. Maximise the total.

## Run

    python3 solution.py

Runs its own tests: the worked examples, the edge cases (empty row, single
balloon, zeros), and 120 random rows cross-checked against the definition — every
bursting order, scored by simulation.

## The interesting part

Choosing which balloon to burst **first** does not decompose the problem. Burst
the middle one and the two halves stop being independent: a balloon on the left
can now be paired with one on the right, so neither side can be solved without
knowing what the other did.

Choosing the **last** one does decompose it. If balloon `i` is the last to burst
inside the open interval `(lo, hi)`, then by that moment everything strictly
between `lo` and `hi` is gone, so `i`'s neighbours are exactly `lo` and `hi` —
known without knowing the order of anything else. And every other balloon in the
interval burst while `i` was still standing, so none of them ever reached across
it. The two sides really are independent:

    best(lo, hi) = max over lo < i < hi of
                       nums[lo] * nums[i] * nums[hi] + best(lo, i) + best(i, hi)

Sentinel `1`s at both ends make `lo` and `hi` always exist. O(n³) time, O(n²)
space, and the same recurrence is written twice — bottom-up over widening
intervals, and top-down with memoisation, which is the shape the insight
actually arrives in.

The tests also pin down a heuristic worth being suspicious of: bursting the
smallest balloon first, on the grounds that it is the cheapest thing to lose as a
multiplier, scores 78 on `[3,1,5,8]` against the optimal 167.
