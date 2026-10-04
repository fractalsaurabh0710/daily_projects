"""
LeetCode 395 — Longest Substring with At Least K Repeating Characters.

Given a string s and an integer k, return the length of the longest substring
in which every character that appears, appears at least k times.

The usual sliding window fails here: the predicate "every character appears
>= k times" is not monotonic. Growing a window can fix a violation (a rare
character picks up more copies) and shrinking can cause one, so there is no
single pointer motion that is always safe. Two ways around that:

1. Divide and conquer. If a character appears fewer than k times anywhere in
   s, it cannot appear in any valid substring. So it is a hard wall: split on
   it and recurse. If no such character exists, all of s is valid.
   O(n * 26) worst case, O(26) recursion depth.

2. Restore monotonicity by fixing the number of distinct characters. For each
   u in 1..26, find the longest window holding exactly u distinct characters,
   all with count >= k. With u pinned, "too many distinct" is monotonic in the
   window's length, so an ordinary two-pointer scan works.
   O(26 * n) time, O(26) space.
"""


def longest_substring_divide(s: str, k: int) -> int:
    if k <= 1:
        return len(s)
    if len(s) < k:
        return 0

    counts = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1

    # Any character below the threshold can never be inside a valid answer.
    for ch, n in counts.items():
        if n < k:
            return max(
                (longest_substring_divide(part, k) for part in s.split(ch)),
                default=0,
            )

    return len(s)


def longest_substring_window(s: str, k: int) -> int:
    if k <= 1:
        return len(s)

    distinct_total = len(set(s))
    best = 0

    for target in range(1, distinct_total + 1):
        counts = {}
        distinct = 0        # characters present in the window
        satisfied = 0       # of those, how many have count >= k
        left = 0

        for right, ch in enumerate(s):
            counts[ch] = counts.get(ch, 0) + 1
            if counts[ch] == 1:
                distinct += 1
            if counts[ch] == k:
                satisfied += 1

            # With `target` pinned, this shrink is monotonic and therefore safe.
            while distinct > target:
                drop = s[left]
                if counts[drop] == k:
                    satisfied -= 1
                counts[drop] -= 1
                if counts[drop] == 0:
                    distinct -= 1
                left += 1

            if distinct == target and satisfied == target:
                best = max(best, right - left + 1)

    return best


def _test():
    cases = [
        ("aaabb", 3, 3),        # "aaa"
        ("ababbc", 2, 5),       # "ababb"
        ("bbaaacbd", 3, 3),     # "aaa"
        ("weitong", 2, 0),      # no character repeats
        ("aaa", 4, 0),          # shorter than k
        ("", 1, 0),
        ("abcdef", 1, 6),       # k == 1 accepts everything
        ("aacbbbdc", 2, 3),     # "bbb" beats "aa" and the split halves
        ("cbaaaabc", 2, 8),     # every character already clears k=2
        ("a" * 50 + "b" + "a" * 60, 5, 60),
    ]
    for s, k, want in cases:
        for fn in (longest_substring_divide, longest_substring_window):
            got = fn(s, k)
            assert got == want, f"{fn.__name__}({s!r}, {k}) = {got}, want {want}"

    # Cross-check the two approaches against a brute force on small inputs.
    import itertools
    import random

    def brute(s, k):
        best = 0
        for i in range(len(s)):
            for j in range(i + 1, len(s) + 1):
                sub = s[i:j]
                if all(sub.count(c) >= k for c in set(sub)):
                    best = max(best, j - i)
        return best

    random.seed(395)
    for _ in range(300):
        s = "".join(random.choice("abc") for _ in range(random.randint(0, 12)))
        k = random.randint(1, 4)
        want = brute(s, k)
        assert longest_substring_divide(s, k) == want, (s, k)
        assert longest_substring_window(s, k) == want, (s, k)

    for n in range(7):
        for tup in itertools.product("ab", repeat=n):
            s = "".join(tup)
            for k in (2, 3):
                want = brute(s, k)
                assert longest_substring_divide(s, k) == want, (s, k)
                assert longest_substring_window(s, k) == want, (s, k)

    print("all tests passed")


if __name__ == "__main__":
    _test()
