"""LeetCode 312 - Burst Balloons.

Balloons in a row carry numbers. Bursting balloon i pays
left * nums[i] * right, where left and right are its *current* neighbours --
the balloons already burst are gone, so the row closes up behind them.
Maximise the total paid over some order of bursting all of them.

The difficulty is that bursting changes the neighbours of everything else, so
there is no clean "solve the left half, solve the right half" split: a balloon
in the left half can end up paired with one in the right half once the middle
is gone. Picking the FIRST balloon to burst therefore does not decompose the
problem.

Picking the LAST one does. If balloon i is the last to burst inside the open
interval (lo, hi), then by that moment everything strictly between lo and hi
is gone, so i's neighbours are exactly lo and hi -- known without knowing the
order of anything else. And every other balloon in the interval burst while i
was still standing, so it never reached across i: the two sides are
independent subproblems of the same shape.

    best(lo, hi) = max over lo < i < hi of
                       nums[lo] * nums[i] * nums[hi]
                     + best(lo, i) + best(i, hi)

with sentinel 1s padded at both ends so lo and hi always exist. O(n^3) time,
O(n^2) space.
"""

from functools import lru_cache
from itertools import permutations


def max_coins(nums):
    """Maximum coins obtainable, via interval DP over the last balloon burst."""
    padded = [1] + [n for n in nums if n != 0] + [1]
    size = len(padded)

    # best[lo][hi] = most coins from bursting everything strictly inside.
    best = [[0] * size for _ in range(size)]

    # Intervals in increasing width; width 2 is the first with an interior.
    for width in range(2, size):
        for lo in range(size - width):
            hi = lo + width
            edges = padded[lo] * padded[hi]
            best[lo][hi] = max(
                edges * padded[last] + best[lo][last] + best[last][hi]
                for last in range(lo + 1, hi)
            )
    return best[0][size - 1]


def max_coins_memo(nums):
    """Same recurrence, written top-down -- the shape the insight comes in."""
    padded = [1] + [n for n in nums if n != 0] + [1]

    @lru_cache(maxsize=None)
    def best(lo, hi):
        if hi - lo < 2:
            return 0
        return max(
            padded[lo] * padded[last] * padded[hi] + best(lo, last) + best(last, hi)
            for last in range(lo + 1, hi)
        )

    return best(0, len(padded) - 1)


def max_coins_bruteforce(nums):
    """Every bursting order, scored by simulation. O(n! * n) -- reference only."""
    indices = range(len(nums))
    totals = []
    for order in permutations(indices):
        row = list(nums)
        alive = [True] * len(nums)
        total = 0
        for i in order:
            left = next((row[j] for j in range(i - 1, -1, -1) if alive[j]), 1)
            right = next((row[j] for j in range(i + 1, len(row)) if alive[j]), 1)
            total += left * row[i] * right
            alive[i] = False
        totals.append(total)
    return max(totals, default=0)


def _test():
    import random

    # LeetCode's examples.
    assert max_coins([3, 1, 5, 8]) == 167
    assert max_coins([1, 5]) == 10

    # Edges: empty, single, and zeros, which pay nothing and only block.
    assert max_coins([]) == 0
    assert max_coins([7]) == 7
    assert max_coins([0, 0]) == 0
    assert max_coins([0, 4, 0]) == 4

    for case in ([3, 1, 5, 8], [1, 5], [7], [], [2, 4, 6], [9, 76, 64, 21]):
        assert max_coins_memo(case) == max_coins(case), case

    # Cross-check both DPs against the definition on small random rows.
    random.seed(312)
    for _ in range(120):
        nums = [random.randint(0, 9) for _ in range(random.randint(0, 6))]
        expected = max_coins_bruteforce(nums)
        assert max_coins(nums) == expected, (nums, max_coins(nums), expected)
        assert max_coins_memo(nums) == expected, nums

    # A greedy "burst the smallest first" heuristic is tempting and wrong.
    def greedy_smallest_first(nums):
        row = list(nums)
        total = 0
        while row:
            i = min(range(len(row)), key=lambda j: row[j])
            left = row[i - 1] if i > 0 else 1
            right = row[i + 1] if i + 1 < len(row) else 1
            total += left * row[i] * right
            row.pop(i)
        return total

    assert greedy_smallest_first([3, 1, 5, 8]) == 78 < 167

    # And it scales: 60 balloons is instant for the DP, hopeless for the
    # 60! orders the brute force would enumerate.
    big = [random.randint(1, 100) for _ in range(60)]
    assert max_coins(big) == max_coins_memo(big) > 0

    print("all tests passed")


if __name__ == "__main__":
    _test()
