"""LeetCode 862 — Shortest Subarray with Sum at Least K.

Given an integer array (negatives allowed) and a target K, find the length of
the shortest contiguous subarray whose sum is >= K, or -1 if none exists.

Negative numbers are the whole difficulty. With all-positive values the plain
two-pointer window works, because growing the window only ever increases the
sum. With negatives, a window's sum is not monotonic in its length, so
shrinking from the left can *raise* the sum and the sliding window loses its
footing.

The fix is to stop thinking about windows and think about prefix sums:

    P[0] = 0,  P[i] = a[0] + ... + a[i-1]
    sum(a[j:i]) = P[i] - P[j]

So the question becomes: for each i, find the largest j < i with
P[j] <= P[i] - K. A monotonic deque of candidate j's does this in O(n), and it
rests on two observations:

  1. If P[j] satisfies the condition for the current i, it will satisfy it for
     every later i' only with a *longer* subarray — so once j produces an
     answer it is useless forever and can be dropped from the front.
  2. If j < i and P[j] >= P[i], then j is dominated: any future i' that j
     could serve, i serves with a sum at least as large and a length strictly
     shorter. So j can be dropped from the back.

What survives is a deque of indices with strictly increasing prefix sums, each
index pushed and popped at most once: O(n) time, O(n) space.
"""

from collections import deque
from itertools import accumulate
from random import randint, seed


def shortest_subarray(nums, k):
    """O(n) monotonic-deque solution. Returns the length, or -1."""
    prefix = [0, *accumulate(nums)]
    best = len(nums) + 1
    candidates = deque()  # indices into prefix, prefix values strictly increasing

    for i, p in enumerate(prefix):
        # Observation 1: front candidates that already reach K are spent.
        while candidates and p - prefix[candidates[0]] >= k:
            best = min(best, i - candidates.popleft())
        # Observation 2: drop candidates this index dominates.
        while candidates and prefix[candidates[-1]] >= p:
            candidates.pop()
        candidates.append(i)

    return best if best <= len(nums) else -1


def shortest_subarray_brute(nums, k):
    """O(n^2) reference used only to check the fast one."""
    n = len(nums)
    best = n + 1
    for start in range(n):
        total = 0
        for end in range(start, n):
            total += nums[end]
            if total >= k:
                best = min(best, end - start + 1)
                break  # extending start..end can only lengthen it
    return best if best <= n else -1


def main():
    # Hand cases, including the ones from the problem statement.
    cases = [
        ([1], 1, 1),
        ([1, 2], 4, -1),
        ([2, -1, 2], 3, 3),
        ([84, -37, 32, 40, 95], 167, 3),
        ([-28, 81, -20, 28, -29], 89, 3),
        ([17, 85, 93, -45, -21], 150, 2),
        # No single element reaches K, but a span crossing the -5 does: the
        # negatives are exactly what break the all-positive sliding window.
        ([10, -5, 10], 15, 3),
        # Everything negative: no subarray can reach a positive K.
        ([-1, -2, -3], 1, -1),
        # K reachable only by the entire array.
        ([1, 1, 1, 1], 4, 4),
    ]
    for nums, k, want in cases:
        got = shortest_subarray(nums, k)
        assert got == want, f"{nums} k={k}: got {got}, want {want}"
    print(f"{len(cases)} hand cases pass")

    # Differential test against the brute force. Small ranges on purpose, so
    # that short answers and -1 both come up often.
    seed(862)
    trials = 4000
    for _ in range(trials):
        n = randint(1, 12)
        nums = [randint(-8, 8) for _ in range(n)]
        k = randint(-3, 20)
        fast, slow = shortest_subarray(nums, k), shortest_subarray_brute(nums, k)
        assert fast == slow, f"{nums} k={k}: fast {fast} != brute {slow}"
    print(f"{trials} random arrays agree with the O(n^2) reference")

    # The deque really is linear: a 200k-element array with a long negative
    # stretch, which is the shape that makes quadratic solutions crawl.
    seed(1)
    big = [randint(-50, 50) for _ in range(200_000)]
    print(f"200k elements, K=1000 -> {shortest_subarray(big, 1000)}")


if __name__ == "__main__":
    main()
