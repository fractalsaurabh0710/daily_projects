"""Suffix automaton: the smallest DFA accepting exactly the suffixes of a string.

Built online, one character at a time, in O(n) for a fixed alphabet. Every state
is an equivalence class of substrings that occur at exactly the same set of end
positions, which is what makes the thing so useful: a single state answers
"how many times does this substring occur", and the states' class sizes sum to
the number of distinct substrings.

Run this file to check those claims against brute force.
"""

from itertools import product
from random import Random


class SuffixAutomaton:
    def __init__(self, text=""):
        # State 0 is the initial state; link[0] = -1 marks the root of the
        # suffix-link tree. length[v] is the longest string reaching v.
        self.length = [0]
        self.link = [-1]
        self.trans = [{}]
        self.cnt = [0]
        self.last = 0
        self._counted = False
        for ch in text:
            self.extend(ch)

    def _add_state(self, length, link, trans, cnt):
        self.length.append(length)
        self.link.append(link)
        self.trans.append(trans)
        self.cnt.append(cnt)
        return len(self.length) - 1

    def extend(self, ch):
        """Append one character, keeping the automaton minimal."""
        cur = self._add_state(self.length[self.last] + 1, -1, {}, 1)
        self._counted = False

        # Walk the suffix links from the previous longest state, wiring up every
        # suffix that has no ch-transition yet.
        p = self.last
        while p != -1 and ch not in self.trans[p]:
            self.trans[p][ch] = cur
            p = self.link[p]

        if p == -1:
            self.link[cur] = 0
        else:
            q = self.trans[p][ch]
            if self.length[p] + 1 == self.length[q]:
                # q is exactly p + ch: it is already the right class.
                self.link[cur] = q
            else:
                # q's class holds strings longer than p + ch, which now end in
                # more places than the short ones do. Split it: `clone` keeps
                # the short strings (and q's outgoing edges), q keeps the long
                # ones. Occurrences are recounted later, so clone starts at 0.
                clone = self._add_state(
                    self.length[p] + 1, self.link[q], dict(self.trans[q]), 0
                )
                while p != -1 and self.trans[p].get(ch) == q:
                    self.trans[p][ch] = clone
                    p = self.link[p]
                self.link[q] = clone
                self.link[cur] = clone

        self.last = cur
        return self

    def _state_of(self, sub):
        v = 0
        for ch in sub:
            if ch not in self.trans[v]:
                return None
            v = self.trans[v][ch]
        return v

    def __contains__(self, sub):
        return self._state_of(sub) is not None

    def _count_occurrences(self):
        # A state's occurrence count is its own (1 if it was a prefix end) plus
        # those of its children in the suffix-link tree. Sorting by length is a
        # topological order of that tree, since link[v] is always shorter.
        if self._counted:
            return
        order = sorted(range(len(self.length)), key=lambda v: -self.length[v])
        totals = list(self.cnt)
        for v in order:
            if self.link[v] > 0 or (self.link[v] == 0 and v != 0):
                if self.link[v] != -1:
                    totals[self.link[v]] += totals[v]
        totals[0] = 0
        self._totals = totals
        self._counted = True

    def occurrences(self, sub):
        """How many times `sub` occurs in the text (0 if never)."""
        if not sub:
            return len(self.length) and 0 or 0
        v = self._state_of(sub)
        if v is None:
            return 0
        self._count_occurrences()
        return self._totals[v]

    def distinct_substrings(self):
        """Number of distinct non-empty substrings of the text."""
        return sum(
            self.length[v] - self.length[self.link[v]]
            for v in range(1, len(self.length))
        )

    def longest_common_substring(self, other):
        """Longest string occurring in both this automaton's text and `other`."""
        v, run, best, best_end = 0, 0, 0, 0
        for i, ch in enumerate(other):
            while v and ch not in self.trans[v]:
                # No edge: fall back along suffix links, which shortens the
                # match to the longest suffix that might extend.
                v = self.link[v]
                run = self.length[v]
            if ch in self.trans[v]:
                v = self.trans[v][ch]
                run += 1
            else:
                v, run = 0, 0
            if run > best:
                best, best_end = run, i + 1
        return other[best_end - best:best_end]


def _brute_substrings(text):
    return {text[i:j] for i in range(len(text)) for j in range(i + 1, len(text) + 1)}


def _brute_occurrences(text, sub):
    return sum(1 for i in range(len(text) - len(sub) + 1) if text[i:i + len(sub)] == sub)


def _brute_lcs(a, b):
    best = ""
    for i in range(len(a)):
        for j in range(i + len(best) + 1, len(a) + 1):
            if a[i:j] in b:
                best = a[i:j]
    return best


def _test():
    rng = Random(20261030)

    # Exhaustive over every short binary string.
    for n in range(1, 11):
        for bits in product("ab", repeat=n):
            text = "".join(bits)
            sam = SuffixAutomaton(text)
            subs = _brute_substrings(text)
            assert sam.distinct_substrings() == len(subs), text
            # The classic size bounds: at most 2n-1 states for n >= 2.
            assert len(sam.length) <= max(2, 2 * n - 1), (text, len(sam.length))

    # Membership and occurrence counts on random strings.
    for _ in range(200):
        text = "".join(rng.choice("abc") for _ in range(rng.randint(1, 60)))
        sam = SuffixAutomaton(text)
        for _ in range(40):
            k = rng.randint(1, 4)
            probe = "".join(rng.choice("abcd") for _ in range(k))
            want = _brute_occurrences(text, probe)
            assert (probe in sam) == (want > 0), (text, probe)
            assert sam.occurrences(probe) == want, (text, probe, want)
        for i in range(len(text)):
            suffix = text[i:]
            assert suffix in sam and sam.occurrences(suffix) >= 1

    # Longest common substring, including after incremental extension.
    for _ in range(150):
        a = "".join(rng.choice("abc") for _ in range(rng.randint(1, 30)))
        b = "".join(rng.choice("abc") for _ in range(rng.randint(1, 30)))
        got = SuffixAutomaton(a).longest_common_substring(b)
        want_len = len(_brute_lcs(a, b))
        assert len(got) == want_len, (a, b, got, want_len)
        assert got in a and got in b

    # Building character by character must match building all at once.
    sam = SuffixAutomaton()
    text = ""
    for ch in "mississippi":
        sam.extend(ch)
        text += ch
        assert sam.distinct_substrings() == len(_brute_substrings(text))

    print("all tests passed")

    sam = SuffixAutomaton("mississippi")
    print()
    print("  text                 mississippi")
    print("  states              ", len(sam.length), "(bound 2n-1 =", 2 * 11 - 1, ")")
    print("  distinct substrings ", sam.distinct_substrings(), "of", 11 * 12 // 2, "positions")
    for probe in ("iss", "ssi", "ppi", "sip", "xyz"):
        print(f"  occurrences({probe!r:7}) {sam.occurrences(probe)}")
    print("  LCS with 'missing'  ", repr(sam.longest_common_substring("missing")))


if __name__ == "__main__":
    _test()
