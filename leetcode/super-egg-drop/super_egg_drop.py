"""LeetCode 887 -- Super Egg Drop.

You have k identical eggs and a building of n floors. An egg dropped from floor
f breaks if f > T and survives otherwise, for some unknown threshold
T in 0..n.  A broken egg is gone; a surviving egg is reusable.  How many drops
are needed in the worst case to pin T exactly?

The obvious DP is over the *state*: dp[k][n] = 1 + min over the first drop x of
max(dp[k-1][x-1], dp[k][n-x]) -- a min over a max, O(k*n^2) and far too slow for
n = 10000.

The trick is to invert the question.  Instead of "how many drops do k eggs need
for n floors", ask "how many floors can k eggs clear in m drops".  Call that
f(k, m).  The first drop either breaks -- leaving k-1 eggs, m-1 drops, and
f(k-1, m-1) floors resolvable below -- or survives, leaving f(k, m-1) above.
Plus the floor just tested:

    f(k, m) = f(k-1, m-1) + f(k, m-1) + 1

No min, no max: the optimal split is not chosen, it *falls out*, because an
optimal strategy is free to put the first drop exactly where the two branches
meet.  Sweep m upward until f(k, m) >= n and that m is the answer.

That recurrence is Pascal's rule in disguise, so f has a closed form:

    f(k, m) = C(m,1) + C(m,2) + ... + C(m,k)

which for k >= m is 2^m - 1 -- plain binary search, as it should be.
"""

from math import comb


def drops_naive(k: int, n: int) -> int:
    """Textbook state DP: O(k*n^2). Reference implementation only."""
    # dp[e][f] = worst-case drops with e eggs and f floors still in play.
    dp = [[0] * (n + 1) for _ in range(k + 1)]
    for f in range(1, n + 1):
        dp[1][f] = f  # one egg: climb from the bottom, no other option
    for e in range(2, k + 1):
        for f in range(1, n + 1):
            best = f
            for x in range(1, f + 1):
                worst = 1 + max(dp[e - 1][x - 1], dp[e][f - x])
                if worst < best:
                    best = worst
            dp[e][f] = best
    return dp[k][n] if k else 0


def floors_covered(k: int, m: int) -> int:
    """f(k, m) by the inverted recurrence -- floors resolvable in m drops."""
    row = [0] * (k + 1)  # row[e] = f(e, drops_so_far)
    for _ in range(m):
        for e in range(k, 0, -1):
            row[e] = row[e - 1] + row[e] + 1
    return row[k]


def drops_fast(k: int, n: int) -> int:
    """O(k * answer) -- the inverted DP, which is what 887 wants."""
    row = [0] * (k + 1)
    m = 0
    while row[k] < n:
        m += 1
        for e in range(k, 0, -1):
            row[e] = row[e - 1] + row[e] + 1
    return m


def drops_binomial(k: int, n: int) -> int:
    """Closed form: smallest m with C(m,1)+...+C(m,k) >= n."""
    cover = lambda m: sum(comb(m, i) for i in range(1, k + 1))
    lo, hi = 1, n
    while lo < hi:
        mid = (lo + hi) // 2
        if cover(mid) >= n:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _test() -> None:
    # Known values from the problem statement and its follow-ups.
    assert drops_fast(1, 2) == 2
    assert drops_fast(2, 6) == 3
    assert drops_fast(3, 14) == 4
    assert drops_fast(2, 100) == 14
    assert drops_fast(2, 1000) == 45
    assert drops_fast(3, 10000) == 40

    # All three routines agree everywhere the slow one is affordable.
    for k in range(1, 7):
        for n in range(1, 81):
            slow = drops_naive(k, n)
            assert drops_fast(k, n) == slow, (k, n)
            assert drops_binomial(k, n) == slow, (k, n)

    # The recurrence and the binomial sum are the same function.
    for k in range(1, 9):
        for m in range(0, 15):
            assert floors_covered(k, m) == sum(comb(m, i) for i in range(1, k + 1))

    # Enough eggs to never run out -> exactly binary search.
    for m in range(1, 13):
        assert floors_covered(m, m) == 2 ** m - 1
        assert drops_fast(m, 2 ** m - 1) == m
    print("all tests pass")


def main() -> None:
    _test()
    print()
    print("floors clearable in m drops -- f(k, m)")
    print("      " + "".join(f"{m:>7}" for m in range(1, 11)))
    for k in range(1, 6):
        print(f"k={k} |" + "".join(f"{floors_covered(k, m):>7}" for m in range(1, 11)))
    print()
    print("drops needed for n = 10000 floors")
    for k in range(1, 9):
        m = drops_fast(k, 10000)
        slack = floors_covered(k, m) - 10000
        print(f"  k={k}: {m:>4} drops   (clears {floors_covered(k, m)}, {slack} to spare)")
    print()
    print("two eggs, 100 floors: 14 drops, first from floor 14 --")
    print("  a break leaves 13 floors for 13 drops; a survival leaves 86 for 13,")
    print("  and 13 drops with 2 eggs clear 13+12+...+1 = 91 >= 86.")


if __name__ == "__main__":
    main()
