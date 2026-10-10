# Shortest Subarray with Sum at Least K

LeetCode 862. Find the length of the shortest contiguous subarray whose sum is
at least `K`, where the array may contain negative numbers.

## Run

    python3 main.py

It runs its own tests: nine hand cases, then 4000 random arrays checked against
an `O(n^2)` reference, then a 200k-element array to show the linear solution
does not care about size.

## The interesting part

With all-positive values this is the textbook two-pointer window. Negatives
kill it, because a window's sum is no longer monotonic in its length — moving
the left edge right can *increase* the sum, so there is nothing to slide
against.

Reframing it in prefix sums fixes that: `sum(a[j:i]) = P[i] - P[j]`, so for
each `i` we want the largest `j` with `P[j] <= P[i] - K`. A deque holding
candidate `j`s with strictly increasing prefix sums answers that in O(n) total,
on two invariants — a candidate that already reaches `K` is spent and leaves
the front, and a candidate with `P[j] >= P[i]` for `j < i` is dominated by `i`
and leaves the back. Each index enters and leaves once.
