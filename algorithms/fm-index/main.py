"""FM-index: substring search inside a compressed-ish permutation of the text.

The Burrows-Wheeler transform rotates a string, sorts the rotations, and keeps
only the last column. That column is reversible on its own, and -- the useful
part -- it answers "how many times does P occur in T?" in O(|P|) time without
ever decompressing the text. Everything here is built from scratch: suffix
array, BWT, rank table, backward search, and position recovery from a sampled
suffix array.

Run: python3 main.py
"""

SENTINEL = "\x00"  # sorts before every real character


def suffix_array(text):
    """O(n log^2 n) prefix doubling. Good enough, and short."""
    n = len(text)
    rank = [ord(c) for c in text]
    sa = list(range(n))
    k = 1
    while True:
        key = lambda i: (rank[i], rank[i + k] if i + k < n else -1)
        sa.sort(key=key)
        new = [0] * n
        for j in range(1, n):
            new[sa[j]] = new[sa[j - 1]] + (key(sa[j]) != key(sa[j - 1]))
        rank = new
        if rank[sa[-1]] == n - 1:
            return sa
        k *= 2


def bwt(text):
    """Last column of the sorted rotation matrix, via the suffix array."""
    t = text + SENTINEL
    sa = suffix_array(t)
    return "".join(t[i - 1] for i in sa), sa


def inverse_bwt(last):
    """Rebuild the text from the last column using the LF mapping.

    The i-th occurrence of c in the last column and the i-th occurrence of c in
    the (sorted) first column are the same rotation, so one array of jumps is
    enough to walk the original string backwards.
    """
    counts = {}
    lf = [0] * len(last)
    first = sorted(last)
    starts, seen = {}, 0
    for c in first:
        if c not in starts:
            starts[c] = seen
        seen += 1
    for i, c in enumerate(last):
        lf[i] = starts[c] + counts.get(c, 0)
        counts[c] = counts.get(c, 0) + 1
    out, row = [], 0  # row 0 is the rotation ending in the sentinel
    for _ in range(len(last) - 1):
        out.append(last[row])
        row = lf[row]
    return "".join(reversed(out))


class FMIndex:
    """Backward search over the BWT, plus sampled positions for locate()."""

    def __init__(self, text, sa_sample=8):
        self.last, sa = bwt(text)
        self.n = len(self.last)
        self.sa_sample = sa_sample
        # keep only every sa_sample-th suffix position; the rest are walked to
        self.sampled = {i: p for i, p in enumerate(sa) if p % sa_sample == 0}
        alphabet = sorted(set(self.last))
        # C[c] = number of characters in the text strictly smaller than c
        total = 0
        self.C = {}
        freq = {c: self.last.count(c) for c in alphabet}
        for c in alphabet:
            self.C[c] = total
            total += freq[c]
        # occ[c][i] = occurrences of c in last[:i]  (one row per character)
        self.occ = {c: [0] * (self.n + 1) for c in alphabet}
        for i, ch in enumerate(self.last):
            for c in alphabet:
                self.occ[c][i + 1] = self.occ[c][i] + (c == ch)

    def _range(self, pattern):
        lo, hi = 0, self.n
        for c in reversed(pattern):
            if c not in self.C:
                return 0, 0
            lo = self.C[c] + self.occ[c][lo]
            hi = self.C[c] + self.occ[c][hi]
            if lo >= hi:
                return 0, 0
        return lo, hi

    def count(self, pattern):
        lo, hi = self._range(pattern)
        return hi - lo

    def locate(self, pattern):
        """Text offsets of every match, recovered by walking LF to a sample."""
        lo, hi = self._range(pattern)
        out = []
        for row in range(lo, hi):
            steps, r = 0, row
            while r not in self.sampled:
                c = self.last[r]
                r = self.C[c] + self.occ[c][r]
                steps += 1
            out.append(self.sampled[r] + steps)
        return sorted(out)


def _test():
    import random

    assert inverse_bwt(bwt("banana")[0]) == "banana"
    assert bwt("banana")[0] == "annb" + SENTINEL + "aa"

    text = "mississippi"
    idx = FMIndex(text, sa_sample=3)
    assert idx.count("iss") == 2
    assert idx.locate("iss") == [1, 4]
    assert idx.count("ssi") == 2
    assert idx.count("zebra") == 0
    assert idx.locate("i") == [1, 4, 7, 10]

    random.seed(7)
    for _ in range(40):
        t = "".join(random.choice("abc") for _ in range(random.randint(1, 60)))
        index = FMIndex(t, sa_sample=random.randint(1, 5))
        assert inverse_bwt(index.last) == t
        for plen in (1, 2, 3):
            for _ in range(5):
                if plen > len(t):
                    continue
                s = random.randint(0, len(t) - plen)
                p = t[s:s + plen]
                want = [i for i in range(len(t) - plen + 1) if t[i:i + plen] == p]
                assert index.count(p) == len(want), (t, p)
                assert index.locate(p) == want, (t, p)
    print("all tests passed")


if __name__ == "__main__":
    _test()
    text = "the quick brown fox jumps over the lazy dog, the quick brown cat"
    idx = FMIndex(text)
    print(f"text ({len(text)} chars): {text}")
    print(f"bwt: {idx.last.replace(SENTINEL, '$')}")
    for p in ("the quick", "brown", "cat", "zebra"):
        print(f"  {p!r:12} count={idx.count(p)} at={idx.locate(p)}")
