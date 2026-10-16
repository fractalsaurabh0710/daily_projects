# Subarrays with K Different Integers (LeetCode 992)

Count the subarrays of an array that contain exactly `k` distinct values.

## Run

    python3 solution.py

Runs its own tests: the worked examples, the edge cases, and 400 random arrays
cross-checked against the O(n^2) definition for every `k` from 1 to 5.

## The interesting part

A sliding window needs a monotone predicate to shrink on, and "exactly `k`
distinct" is not one — growing the window can overshoot `k`, shrinking it can
undershoot, and the window never sees the valid subarrays in between. Two ways
out, both linear:

- **Subtraction.** "At most `k` distinct" *is* monotone, so one window counts it
  directly by adding `right - left + 1` per step. Then
  `exactly(k) = atMost(k) - atMost(k-1)`.
- **Three pointers.** One pass with two left edges. `narrow` is the leftmost
  start whose window holds at most `k` distinct; `wide` is pushed as far right as
  it will go while the window still holds exactly `k`, which it can do whenever
  the value at `wide` appears again further right. Every start in
  `[narrow, wide]` is then a valid subarray ending here, so this right edge
  contributes `wide - narrow + 1`.

The second is the one with a trap: `wide` has to be brought down to `k` distinct
before it can be pushed past duplicates. Skip that and it lags behind `narrow`,
producing a negative contribution — which the random cross-check catches
immediately on `[1,2,1,2,3]` with `k = 2`.
