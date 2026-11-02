"""Aho-Corasick: find every occurrence of every pattern in one pass over the text.

Built in two stages. First a trie of the patterns, where each node has only the
edges that a pattern actually spelled. Then a BFS that gives every node a
*failure* link -- the node spelling the longest proper suffix of this node's
string that is itself a node -- and uses those links to fill in the missing
edges, so that after the BFS every node has an edge for every character in the
alphabet. The scan is then a plain table walk: one lookup per character, never a
step backwards, never a fallback loop.

The subtlety is that a failure link also inherits *matches*. "he" is a suffix of
"she", so arriving at the node for "she" must report "he" too. Each node keeps a
link to the nearest ancestor-by-failure that ends a pattern, and reporting walks
that short chain -- which is what makes the output size, not the text length,
the only thing that can make matching slow.
"""

from collections import deque


class AhoCorasick:
    def __init__(self, patterns):
        # Node i: goto[i] maps char -> node, out[i] lists pattern indices ending here.
        self.goto = [{}]
        self.out = [[]]
        self.fail = [0]
        self.out_link = [-1]          # nearest failure-ancestor that ends a pattern
        self.patterns = list(patterns)

        for idx, pat in enumerate(self.patterns):
            if not pat:
                raise ValueError("empty pattern matches everywhere; refuse it")
            node = 0
            for ch in pat:
                nxt = self.goto[node].get(ch)
                if nxt is None:
                    nxt = len(self.goto)
                    self.goto.append({})
                    self.out.append([])
                    self.fail.append(0)
                    self.out_link.append(-1)
                    self.goto[node][ch] = nxt
                node = nxt
            self.out[node].append(idx)

        self._build_links()

    def _build_links(self):
        """BFS in order of depth: a node's failure link always points to a
        shallower node, so it is already final by the time we need it."""
        queue = deque()
        for ch, child in self.goto[0].items():
            self.fail[child] = 0
            queue.append(child)

        while queue:
            node = queue.popleft()
            f = self.fail[node]
            # Matches reachable by dropping a prefix: either f itself ends a
            # pattern, or f's own chain does.
            self.out_link[node] = f if self.out[f] else self.out_link[f]

            for ch, child in list(self.goto[node].items()):
                # The child's failure target is where the parent's failure node
                # goes on the same character -- and that edge is already filled
                # in, because fail[node] is shallower than node.
                self.fail[child] = self.goto[f].get(ch, 0) if node else 0
                queue.append(child)

            # Densify: borrow every edge this node lacks from its failure node.
            for ch, target in self.goto[f].items():
                self.goto[node].setdefault(ch, target)

    def find_all(self, text):
        """Yield (end_index_exclusive, pattern_index) for every occurrence."""
        node = 0
        for i, ch in enumerate(text):
            node = self.goto[node].get(ch, 0)
            reporter = node
            while reporter != -1:
                for idx in self.out[reporter]:
                    yield i + 1, idx
                reporter = self.out_link[reporter]

    def matches(self, text):
        """Occurrences as (start, pattern) pairs, sorted."""
        return sorted(
            (end - len(self.patterns[idx]), self.patterns[idx])
            for end, idx in self.find_all(text)
        )


def brute_force(patterns, text):
    found = []
    for pat in patterns:
        start = text.find(pat)
        while start != -1:
            found.append((start, pat))
            start = text.find(pat, start + 1)
    return sorted(found)


def _test():
    # The classic example: overlapping patterns, one a suffix of another.
    ac = AhoCorasick(["he", "she", "his", "hers"])
    assert ac.matches("ushers") == [(1, "she"), (2, "he"), (2, "hers")]

    # A pattern wholly inside another, found at the same position.
    ac = AhoCorasick(["a", "ab", "abc"])
    assert ac.matches("abcd") == [(0, "a"), (0, "ab"), (0, "abc")]

    # Overlapping copies of one pattern.
    ac = AhoCorasick(["aa"])
    assert ac.matches("aaaa") == [(0, "aa"), (1, "aa"), (2, "aa")]

    # Nothing to find.
    assert AhoCorasick(["xyz"]).matches("abcabc") == []

    # No edge for the first character: must stay at the root, not crash.
    assert AhoCorasick(["bb"]).matches("aaab") == []

    try:
        AhoCorasick([""])
    except ValueError:
        pass
    else:
        raise AssertionError("empty pattern should be rejected")

    # Randomised: agree with naive search on a small alphabet, where
    # overlaps and suffix relations happen constantly.
    import random
    rng = random.Random(20261024)
    for _ in range(400):
        alphabet = "ab" if rng.random() < 0.5 else "abc"
        pats = list({
            "".join(rng.choice(alphabet) for _ in range(rng.randint(1, 4)))
            for _ in range(rng.randint(1, 6))
        })
        text = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 40)))
        assert AhoCorasick(pats).matches(text) == brute_force(pats, text), (pats, text)

    print("all tests passed")


if __name__ == "__main__":
    _test()

    patterns = ["he", "she", "his", "hers", "her"]
    text = "ushers, he said, and his hershey bar"
    ac = AhoCorasick(patterns)
    print(f"\npatterns: {patterns}")
    print(f"text:     {text!r}\n")
    for start, pat in ac.matches(text):
        print(f"  {start:>3}  {' ' * start}{pat}")
    print(f"\n{len(ac.goto)} nodes, one table lookup per character, "
          f"{len(text)} characters scanned once")
