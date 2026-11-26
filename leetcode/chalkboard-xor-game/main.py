"""LeetCode 810 - Chalkboard XOR Game.

Numbers sit on a chalkboard. Players alternate erasing exactly one of them, and
whoever's erasure leaves the XOR of everything remaining equal to zero loses.
A player who *starts* their turn with the XOR already zero wins on the spot.
Alice moves first; does she win under perfect play?

The accepted answer is one line with no search in it:

    alice wins  <=>  xor(nums) == 0  or  len(nums) is even

Why the parity half is true, in two steps.

1. If n is even and the XOR t is nonzero, Alice always has a *safe* erasure.
   An erasure of x is suicide exactly when t ^ x == 0, i.e. x == t. So the
   only way to be stuck is for every number on the board to equal t -- and the
   XOR of an even count of equal values is 0, contradicting t != 0.

2. So Alice never has to kill herself, and every safe move hands Bob an odd
   board with nonzero XOR. Bob's board is nonempty (the empty board has XOR 0,
   which is a win for whoever faces it), so by induction on n he is in the
   mirror-image of step 1 with the parity against him: eventually a player on
   an odd board finds every number equal to t and must erase it.

A formula cannot test itself, so the claim below is checked against a full
game-tree search over every reachable multiset.
"""

from functools import lru_cache, reduce
from itertools import combinations_with_replacement
from operator import xor


def alice_wins(nums):
    """O(n) answer: the whole problem, once the parity argument is believed."""
    return reduce(xor, nums, 0) == 0 or len(nums) % 2 == 0


def alice_wins_naive(nums):
    """The rule you write down before noticing parity matters at all."""
    return reduce(xor, nums, 0) == 0


@lru_cache(maxsize=None)
def search(state):
    """True if the player about to move on `state` (a sorted tuple) wins."""
    total = reduce(xor, state, 0)
    if total == 0:
        return True                      # includes the empty board
    for x in sorted(set(state)):
        rest = list(state)
        rest.remove(x)
        rest = tuple(rest)
        if reduce(xor, rest, 0) == 0:
            continue                     # erasing x loses immediately
        if not search(rest):
            return True
    return False                         # every erasure is suicide


def positions(values, max_n):
    for n in range(1, max_n + 1):
        for combo in combinations_with_replacement(values, n):
            yield combo


def main():
    for nums, expected in (([1, 1, 2], False), ([0, 1], True), ([1, 2, 3], True)):
        got = alice_wins(nums)
        assert got == expected, (nums, got, expected)
        assert search(tuple(sorted(nums))) == expected, nums
    print("problem-statement examples: 3/3")

    values = (0, 1, 2, 3)
    max_n = 7
    total = disagree = naive_wrong = 0
    stuck_even = 0
    even_nonzero = 0

    for state in positions(values, max_n):
        total += 1
        truth = search(tuple(sorted(state)))
        if alice_wins(state) != truth:
            disagree += 1
            print("formula disagrees on", state)
        if alice_wins_naive(state) != truth:
            naive_wrong += 1

        t = reduce(xor, state, 0)
        if len(state) % 2 == 0 and t != 0:
            even_nonzero += 1
            if all(x == t for x in state):      # step 1's impossible case
                stuck_even += 1

    print(f"positions searched:      {total} multisets over {values}, n <= {max_n}")
    print(f"formula vs game tree:    {total - disagree}/{total} agree")
    print(f"ignoring parity is wrong on {naive_wrong} of them "
          f"({100 * naive_wrong / total:.1f}%)")
    print(f"even boards, nonzero xor: {even_nonzero}, of which stuck: {stuck_even}")

    # The parity half only bites when the XOR is nonzero; show the split.
    odd_loss = sum(1 for s in positions(values, max_n)
                   if len(s) % 2 == 1 and reduce(xor, s, 0) != 0
                   and not search(tuple(sorted(s))))
    odd_nonzero = sum(1 for s in positions(values, max_n)
                      if len(s) % 2 == 1 and reduce(xor, s, 0) != 0)
    print(f"odd boards, nonzero xor:  {odd_nonzero}, Alice loses all "
          f"{odd_loss} of them")

    assert disagree == 0
    assert stuck_even == 0, "step 1 claims an even board with nonzero xor is never stuck"
    assert odd_loss == odd_nonzero
    print("\nall checks passed")


if __name__ == "__main__":
    main()
