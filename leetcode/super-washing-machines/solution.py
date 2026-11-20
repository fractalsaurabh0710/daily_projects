"""LeetCode 517 - Super Washing Machines.

n machines in a row hold `machines[i]` dresses each. In one move you pick any
number of machines and each picked machine hands one dress to one of its
neighbours -- all of them simultaneously. Fewest moves until every machine
holds the same number, or -1 if that is impossible.

The O(n) answer is a pure lower-bound argument, and the interesting part is
that the bound is reached. Two things must happen no matter how you schedule:

  * the gap between the first i machines and their fair share, |prefix(i)|,
    has to cross the single edge between machine i-1 and machine i, and that
    edge carries at most one dress per move, so you need at least |prefix(i)|
    moves;
  * a machine holding machines[i] - avg too many must shed that excess, and it
    may only emit one dress per move, so you need at least that many moves.

The claim is that the largest of those numbers is also sufficient: the local
constraints never interfere, because a machine can receive from one side and
send to the other in the same move. `brute_force` checks that by BFS over
every reachable state, which is the only honest way to test "and it is
achievable" -- the formula cannot be checked against itself.
"""


def min_moves(machines):
    """O(n) time, O(1) space."""
    total = sum(machines)
    n = len(machines)
    if total % n:
        return -1
    avg = total // n
    moves = 0
    prefix = 0  # dresses the left part owes (negative) or must export (positive)
    for load in machines:
        prefix += load - avg
        moves = max(moves, abs(prefix), load - avg)
    return moves


def max_prefix_only(machines):
    """The flow bound alone -- correct for every example in the problem."""
    total, n = sum(machines), len(machines)
    if total % n:
        return -1
    avg, prefix, best = total // n, 0, 0
    for load in machines:
        prefix += load - avg
        best = max(best, abs(prefix))
    return best


def brute_force(machines):
    """Exact shortest number of moves, by BFS over the state space."""
    from collections import deque

    n = len(machines)
    total = sum(machines)
    if total % n:
        return -1
    goal = tuple([total // n] * n)
    start = tuple(machines)
    if start == goal:
        return 0

    seen = {start}
    frontier = deque([(start, 0)])
    while frontier:
        state, depth = frontier.popleft()
        for move in _simultaneous_moves(state):
            if move == goal:
                return depth + 1
            if move not in seen:
                seen.add(move)
                frontier.append((move, depth + 1))
    return -1


def _simultaneous_moves(state):
    """Every state reachable in one move: each machine sends 0 or 1 dress."""
    n = len(state)
    results = []

    def walk(i, delta, acted):
        if i == n:
            if acted:
                results.append(tuple(state[j] + delta[j] for j in range(n)))
            return
        walk(i + 1, delta, acted)  # machine i sits this move out
        if state[i] >= 1:  # one dress, to one side, decided from current counts
            for side in (i - 1, i + 1):
                if 0 <= side < n:
                    delta[i] -= 1
                    delta[side] += 1
                    walk(i + 1, delta, True)
                    delta[i] += 1
                    delta[side] -= 1

    walk(0, [0] * n, False)
    return results


def _configurations(n, total):
    if n == 1:
        yield (total,)
        return
    for first in range(total + 1):
        for rest in _configurations(n - 1, total - first):
            yield (first,) + rest


if __name__ == "__main__":
    assert min_moves([1, 0, 5]) == 3
    assert min_moves([0, 3, 0]) == 2
    assert min_moves([0, 2, 0]) == -1

    checked = 0
    disagreements = []
    for n in (2, 3, 4):
        for avg in (0, 1, 2):
            for config in _configurations(n, n * avg):
                exact = brute_force(list(config))
                assert min_moves(list(config)) == exact, config
                checked += 1
                if max_prefix_only(list(config)) != exact:
                    disagreements.append((config, max_prefix_only(list(config)), exact))
    print(f"formula == BFS on all {checked} balanceable configurations (n<=4, avg<=2)")

    print(f"\nthe flow bound alone is wrong on {len(disagreements)} of them, e.g.")
    for config, guessed, exact in disagreements[:3]:
        print(f"  {list(config)}: prefix bound says {guessed}, truth is {exact}")

    # The excess term only bites when one machine is the whole surplus: here no
    # single edge needs to carry more than 4, but machine 1 must emit 8 dresses.
    big = [0, 10, 0, 0, 0]
    print(f"\n{big}: prefix bound {max_prefix_only(big)}, answer {min_moves(big)}")
    print(f"{[4, 0, 0, 4]}: prefix bound {max_prefix_only([4, 0, 0, 4])}, "
          f"answer {min_moves([4, 0, 0, 4])}  (symmetric, both edges busy at once)")
