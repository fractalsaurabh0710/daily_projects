"""LeetCode 992 - Subarrays with K Different Integers.

Count the subarrays of `nums` containing exactly `k` distinct values.

The obstacle is that "exactly k distinct" is not a monotone predicate, so the
usual sliding window has nothing to shrink on: growing the window can push the
distinct count above k, but shrinking it can drop below k, and the window never
learns which subarrays in between were valid.

Two ways around that, both O(n):

  1. `exactly_k_by_subtraction` - "at most k distinct" IS monotone, so a window
     counts it directly. exactly(k) = atMost(k) - atMost(k-1).

  2. `exactly_k_three_pointer` - keep two left edges in one pass. `narrow` is
     the leftmost start whose window has <= k distinct values; `wide` is the
     leftmost start that still has exactly k. Every start in [narrow, wide)
     gives a valid subarray ending at the current right edge, so the count for
     this right edge is wide - narrow.
"""

from collections import defaultdict


def at_most_k_distinct(nums, k):
    """Number of subarrays with at most k distinct values."""
    if k <= 0:
        return 0
    counts = defaultdict(int)
    total = 0
    left = 0
    for right, value in enumerate(nums):
        counts[value] += 1
        while len(counts) > k:
            counts[nums[left]] -= 1
            if counts[nums[left]] == 0:
                del counts[nums[left]]
            left += 1
        # Every start in [left, right] yields a window with <= k distinct.
        total += right - left + 1
    return total


def exactly_k_by_subtraction(nums, k):
    return at_most_k_distinct(nums, k) - at_most_k_distinct(nums, k - 1)


def exactly_k_three_pointer(nums, k):
    """Single pass: both left edges advance monotonically, so still O(n)."""
    narrow_counts = defaultdict(int)  # window [narrow, right], <= k distinct
    wide_counts = defaultdict(int)    # window [wide, right],   == k distinct
    narrow = wide = 0
    total = 0
    for right, value in enumerate(nums):
        narrow_counts[value] += 1
        wide_counts[value] += 1

        # narrow: smallest start keeping the distinct count at or below k.
        while len(narrow_counts) > k:
            narrow_counts[nums[narrow]] -= 1
            if narrow_counts[nums[narrow]] == 0:
                del narrow_counts[nums[narrow]]
            narrow += 1

        # wide: largest start still holding exactly k distinct values. It
        # first has to come down to k like narrow did, then it keeps going for
        # as long as the value it would drop is duplicated further right.
        while len(wide_counts) > k or (
            len(wide_counts) == k and wide_counts[nums[wide]] > 1
        ):
            wide_counts[nums[wide]] -= 1
            if wide_counts[nums[wide]] == 0:
                del wide_counts[nums[wide]]
            wide += 1

        if len(narrow_counts) == k:
            total += wide - narrow + 1
    return total


def brute_force(nums, k):
    total = 0
    for i in range(len(nums)):
        seen = set()
        for j in range(i, len(nums)):
            seen.add(nums[j])
            if len(seen) == k:
                total += 1
            elif len(seen) > k:
                break
    return total


def _test():
    cases = [
        ([1, 2, 1, 2, 3], 2, 7),
        ([1, 2, 1, 3, 4], 3, 3),
        ([1, 1, 1, 1], 1, 10),
        ([1, 2, 3, 4], 5, 0),
        ([], 1, 0),
        ([5], 1, 1),
    ]
    for nums, k, expected in cases:
        assert exactly_k_by_subtraction(nums, k) == expected, (nums, k)
        assert exactly_k_three_pointer(nums, k) == expected, (nums, k)

    # Both O(n) methods must agree with the O(n^2) definition everywhere.
    import random
    random.seed(992)
    for _ in range(400):
        n = random.randint(0, 14)
        alphabet = random.randint(1, 5)
        nums = [random.randint(1, alphabet) for _ in range(n)]
        for k in range(1, 6):
            expected = brute_force(nums, k)
            assert exactly_k_by_subtraction(nums, k) == expected, (nums, k)
            assert exactly_k_three_pointer(nums, k) == expected, (nums, k)

    print("all tests passed")


if __name__ == "__main__":
    _test()
