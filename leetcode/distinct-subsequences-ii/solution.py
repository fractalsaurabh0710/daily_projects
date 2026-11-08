"""LeetCode 940 - Distinct Subsequences II.

Count the distinct non-empty subsequences of a string, modulo 1e9+7.

The whole problem is the word *distinct*. Counting subsequences with repeats is
trivial: there are 2**n - 1 non-empty ones. The moment characters repeat, two
different index sets can spell the same string, and a counter that cannot see
the string it just built will double-count them.

The fix is to count by *last character* instead of by index set. Let end[c] be
the number of distinct subsequences whose final character is c. Appending a new
character x to every distinct subsequence so far (plus the empty one) produces
exactly the distinct subsequences ending in x:

    end[x] = 1 + sum(end.values())

and it *overwrites* the old end[x] rather than adding to it. That overwrite is
the dedup. Anything that used to end in x is also reachable by taking the same
subsequence and swapping in this later x, so the old set is a subset of the new
one and must not be counted twice.

Total answer: sum(end.values()).
"""

MOD = 10**9 + 7


def distinct_subseq(s: str, mod: int = MOD) -> int:
    """O(n) time, O(alphabet) space."""
    end = {}
    for ch in s:
        end[ch] = (1 + sum(end.values())) % mod
    return sum(end.values()) % mod


def distinct_subseq_running(s: str, mod: int = MOD) -> int:
    """Same recurrence with the sum carried instead of recomputed.

    total' = 2 * total + 1 - end[x], since the new end[x] is total + 1 and the
    old one leaves the running total.
    """
    total = 0
    end = {}
    for ch in s:
        new_end = (total + 1) % mod
        total = (total + new_end - end.get(ch, 0)) % mod
        end[ch] = new_end
    return total % mod


def brute(s: str) -> int:
    """Materialise every distinct subsequence. Exponential - small inputs only."""
    seen = {""}
    for ch in s:
        seen |= {sub + ch for sub in seen}
    return len(seen) - 1  # drop the empty subsequence


def _tests() -> None:
    # LeetCode's own examples.
    assert distinct_subseq("abc") == 7          # every non-empty subset, all distinct
    assert distinct_subseq("aba") == 6          # "a","b","ab","ba","aa","aba"
    assert distinct_subseq("aaa") == 3          # "a","aa","aaa"
    assert distinct_subseq("") == 0

    # 2**n - 1 when every character is unique.
    for n in range(1, 11):
        unique = "abcdefghij"[:n]
        assert distinct_subseq(unique) == 2**n - 1, unique

    # A single repeated character is the degenerate opposite: n, not 2**n - 1.
    assert distinct_subseq("z" * 50) == 50

    # Both implementations agree with brute force on *every* string of length
    # <= 12 over a 2-letter alphabet - 8190 strings, where the double-counting
    # trap is at its densest.
    from itertools import product

    for n in range(13):
        for tup in product("ab", repeat=n):
            s = "".join(tup)
            expected = brute(s)
            if distinct_subseq(s) != expected:
                raise AssertionError(f"dict form wrong on {s!r}")
            if distinct_subseq_running(s) != expected:
                raise AssertionError(f"running form wrong on {s!r}")

    # Randomised cross-check over a 3-letter alphabet, seeded for repeatability.
    import random

    rng = random.Random(940)
    for _ in range(300):
        s = "".join(rng.choice("abc") for _ in range(rng.randint(0, 14)))
        expected = brute(s)
        assert distinct_subseq(s) == expected, s
        assert distinct_subseq_running(s) == expected, s

    # The modulus actually engages: 1000 distinct-ish characters overflow it.
    big = "abcdefghijklmnopqrstuvwxyz" * 40
    assert distinct_subseq(big) == distinct_subseq_running(big)
    assert 0 <= distinct_subseq(big) < MOD

    print("all tests passed")


def _demo() -> None:
    print("\nhow much 'distinct' costs, as a string repeats itself more:")
    print(f"{'string':<16}{'distinct':>12}{'2**n - 1':>14}")
    for s in ["abcdefgh", "abcabcab", "aabbccdd", "abababab", "aaaabbbb", "aaaaaaaa"]:
        print(f"{s:<16}{distinct_subseq(s):>12}{2 ** len(s) - 1:>14}")

    print("\nthe overwrite in slow motion, for 'aba':")
    end = {}
    for ch in "aba":
        before = dict(end)
        end[ch] = 1 + sum(end.values())
        print(f"  read {ch!r}: end[{ch!r}] {before.get(ch, 0)} -> {end[ch]}"
              f"   state={end}   total={sum(end.values())}")


if __name__ == "__main__":
    _tests()
    _demo()
