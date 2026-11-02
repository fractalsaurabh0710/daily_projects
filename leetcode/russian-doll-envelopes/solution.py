"""LeetCode 354 - Russian Doll Envelopes.

Each envelope is (width, height). One fits inside another only if BOTH of its
dimensions are strictly smaller. How many can be nested?

In one dimension this is just the longest strictly increasing subsequence, and
LIS has a famous O(n log n) solution. The obvious move is to sort by width and
run LIS on the heights -- which is right, but only after one detail is settled.

Sorting by width does not remove ties: two envelopes can share a width, and
those two can never nest, because "strictly smaller" has to hold in both
dimensions. If a tied group is sorted by height ASCENDING, the LIS pass is
free to pick several heights out of that one group -- (3,1) then (3,2) -- and
report a chain that does not exist.

The fix costs nothing: within a width, sort the heights DESCENDING.

    (3,5) (3,2) (3,1)

Now the group is strictly decreasing in height, so no increasing subsequence
can take two of its members, and the LIS over heights can only ever use one
envelope per width. The ordering does the constraint's work for it.

    sort by (w asc, h desc), then LIS over the heights -- O(n log n).

`max_envelopes_dp` below is the O(n^2) pairwise-comparison version, kept as an
independent oracle: it never sorts, so it cannot inherit the tiebreak bug, and
the randomised test checks the fast version against it.
"""

from bisect import bisect_left
from random import randint, seed


def max_envelopes(envelopes):
    """Longest nesting chain, via sort + patience LIS. O(n log n)."""
    if not envelopes:
        return 0

    # Width ascending; height DESCENDING inside a width, so a tied group can
    # contribute at most one envelope to an increasing run of heights.
    ordered = sorted(envelopes, key=lambda e: (e[0], -e[1]))

    # tails[k] = smallest height that can end a chain of length k + 1 seen so
    # far. Strictly increasing, so binary search applies.
    tails = []
    for _, height in ordered:
        slot = bisect_left(tails, height)
        if slot == len(tails):
            tails.append(height)
        else:
            tails[slot] = height
    return len(tails)


def max_envelopes_dp(envelopes):
    """Same answer by comparing every pair directly. O(n^2), no sorting.

    Written as recursion with a memo rather than a loop over indices: "fits
    inside" is a strict partial order, so it is acyclic and the recursion
    terminates, but it is NOT the array order -- a left-to-right single pass
    would read a best[j] that had not been settled yet and undercount.
    """
    count = len(envelopes)
    memo = {}

    def longest_ending_at(i):
        if i not in memo:
            wi, hi = envelopes[i]
            memo[i] = 1 + max(
                (
                    longest_ending_at(j)
                    for j in range(count)
                    if envelopes[j][0] < wi and envelopes[j][1] < hi
                ),
                default=0,
            )
        return memo[i]

    return max((longest_ending_at(i) for i in range(count)), default=0)


def max_envelopes_ascending_tiebreak(envelopes):
    """The buggy variant: identical, but ties sort by height ascending.

    Kept only so the test can show the tiebreak is load-bearing rather than
    cosmetic.
    """
    tails = []
    for _, height in sorted(envelopes):
        slot = bisect_left(tails, height)
        if slot == len(tails):
            tails.append(height)
        else:
            tails[slot] = height
    return len(tails)


def _test():
    # LeetCode's own examples.
    assert max_envelopes([[5, 4], [6, 4], [6, 7], [2, 3]]) == 3  # 2,3 -> 5,4 -> 6,7
    assert max_envelopes([[1, 1], [1, 1], [1, 1]]) == 1

    # Degenerate shapes.
    assert max_envelopes([]) == 0
    assert max_envelopes([[7, 7]]) == 1
    assert max_envelopes([[4, 5], [4, 6], [6, 7], [2, 3], [1, 1]]) == 4

    # A full chain and a fully incomparable set.
    chain = [[i, i] for i in range(1, 51)]
    assert max_envelopes(chain) == 50
    antichain = [[i, 50 - i] for i in range(50)]
    assert max_envelopes(antichain) == 1

    # The tiebreak matters: one width, three heights, none nesting.
    one_width = [[3, 1], [3, 2], [3, 5]]
    assert max_envelopes(one_width) == 1
    assert max_envelopes_ascending_tiebreak(one_width) == 3  # wrong, as designed

    # Randomised cross-check against the pairwise oracle, with a small
    # coordinate range so ties are common rather than rare.
    seed(354)
    for _ in range(400):
        size = randint(0, 40)
        case = [[randint(1, 8), randint(1, 8)] for _ in range(size)]
        assert max_envelopes(case) == max_envelopes_dp(case), case

    # And once at a size the O(n^2) oracle would not enjoy.
    seed(1)
    big = [[randint(1, 10**5), randint(1, 10**5)] for _ in range(100_000)]
    print("100k envelopes ->", max_envelopes(big), "deep")

    print("all tests passed")


if __name__ == "__main__":
    _test()
