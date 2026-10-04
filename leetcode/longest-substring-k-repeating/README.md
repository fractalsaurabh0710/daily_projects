# Longest Substring with At Least K Repeating Characters

[LeetCode 395](https://leetcode.com/problems/longest-substring-with-at-least-k-repeating-characters/).
Find the longest substring of `s` in which every character present appears at
least `k` times. Two solutions, plus a brute-force cross-check.

## Run

    python3 main.py

Runs both implementations against hand-written cases, 300 random strings, and
every string over `{a, b}` up to length 6, all verified against brute force.

## The interesting bit

A plain sliding window does not work, because the predicate is not monotonic:
extending a window can *fix* a violation (a rare character gains copies) and
shrinking can *create* one, so no pointer motion is always safe.

- **Divide and conquer** sidesteps it. A character appearing fewer than `k`
  times in the whole string cannot appear in any valid substring, so it is a
  wall — split on it and recurse. No walls means the whole string is valid.
- **Fixed distinct count** restores monotonicity. Pin the number of distinct
  characters to `u` and sweep `u = 1..26`; with `u` fixed, "too many distinct"
  *is* monotonic in window length, so a normal two-pointer scan is correct.

O(26n) either way, but for different reasons: recursion depth in the first,
an explicit outer loop in the second.
