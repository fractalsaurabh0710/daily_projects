"""An indexable skip list: a sorted sequence with O(log n) lookup by *value*
and O(log n) lookup by *position*.

A plain skip list gives you a sorted set with probabilistic balancing and no
rotations. The extra trick here is that every forward pointer also stores its
*span* -- how many positions it jumps over. Spans turn the same tower of
pointers into an order-statistic structure: `sl[k]` finds the k-th smallest and
`sl.rank(x)` counts the elements below x, both without walking the bottom level.

Duplicates are allowed, so this is a sorted multiset / sorted list.
"""

import random

MAX_LEVEL = 20          # supports ~2^20 elements comfortably
PROMOTE = 0.5           # probability a node grows one more level


class _Node:
    __slots__ = ("value", "forward", "span")

    def __init__(self, value, level):
        self.value = value
        self.forward = [None] * level
        # span[i] == (position of forward[i]) - (position of self);
        # for a pointer off the end, the distance to one-past-the-last element.
        self.span = [1] * level


class SkipList:
    def __init__(self, iterable=(), seed=None):
        self._rng = random.Random(seed)
        self._head = _Node(None, MAX_LEVEL)
        self._size = 0
        self.comparisons = 0            # instrumentation for the tests below
        for value in iterable:
            self.insert(value)

    def __len__(self):
        return self._size

    def __iter__(self):
        node = self._head.forward[0]
        while node is not None:
            yield node.value
            node = node.forward[0]

    def __repr__(self):
        return "SkipList(%r)" % (list(self),)

    def _random_level(self):
        level = 1
        while level < MAX_LEVEL and self._rng.random() < PROMOTE:
            level += 1
        return level

    def _descend(self, value):
        """Walk down to the last node whose value is < `value`.

        Returns (chain, positions): chain[i] is that node as seen from level i,
        positions[i] its 0-based position (the head sits at -1).
        """
        chain = [self._head] * MAX_LEVEL
        positions = [-1] * MAX_LEVEL
        node, pos = self._head, -1
        for level in reversed(range(MAX_LEVEL)):
            nxt = node.forward[level]
            while nxt is not None:
                self.comparisons += 1
                if not nxt.value < value:
                    break
                pos += node.span[level]
                node = nxt
                nxt = node.forward[level]
            chain[level] = node
            positions[level] = pos
        return chain, positions

    def insert(self, value):
        chain, positions = self._descend(value)
        new_pos = positions[0] + 1
        height = self._random_level()
        new = _Node(value, height)
        for level in range(height):
            prev = chain[level]
            old_span = prev.span[level]
            new.forward[level] = prev.forward[level]
            prev.forward[level] = new
            prev.span[level] = new_pos - positions[level]
            new.span[level] = old_span - prev.span[level] + 1
        for level in range(height, MAX_LEVEL):
            chain[level].span[level] += 1   # it now steps over one more node
        self._size += 1

    def remove(self, value):
        """Remove one occurrence of `value`; return True if it was there."""
        chain, _ = self._descend(value)
        target = chain[0].forward[0]
        if target is None or target.value != value:
            return False
        for level in range(MAX_LEVEL):
            prev = chain[level]
            if prev.forward[level] is target:
                prev.span[level] += target.span[level] - 1
                prev.forward[level] = target.forward[level]
            else:
                prev.span[level] -= 1
        self._size -= 1
        return True

    def __contains__(self, value):
        node = self._descend(value)[0][0].forward[0]
        return node is not None and node.value == value

    def rank(self, value):
        """How many elements compare strictly less than `value`."""
        return self._descend(value)[1][0] + 1

    def __getitem__(self, index):
        if index < 0:
            index += self._size
        if not 0 <= index < self._size:
            raise IndexError("index out of range")
        node, pos = self._head, -1
        for level in reversed(range(MAX_LEVEL)):
            nxt = node.forward[level]
            while nxt is not None and pos + node.span[level] <= index:
                pos += node.span[level]
                node = nxt
                nxt = node.forward[level]
        return node.value

    def _tower_heights(self):
        heights = []
        node = self._head.forward[0]
        while node is not None:
            heights.append(len(node.forward))
            node = node.forward[0]
        return heights


def _test():
    rng = random.Random(7)

    # 1. Mirror a plain sorted list through a few thousand mixed operations.
    sl, ref = SkipList(seed=1), []
    for _ in range(4000):
        if ref and rng.random() < 0.35:
            victim = rng.choice(ref)
            assert sl.remove(victim) is True
            ref.remove(victim)
        else:
            v = rng.randrange(400)      # small range => plenty of duplicates
            sl.insert(v)
            ref.append(v)
        ref.sort()
        assert len(sl) == len(ref)
    assert list(sl) == ref
    assert sl.remove(10 ** 6) is False

    # 2. Positions and ranks agree with the reference list everywhere.
    for i in range(len(ref)):
        assert sl[i] == ref[i], i
    assert sl[-1] == ref[-1]
    for v in range(-1, 401, 7):
        assert sl.rank(v) == sum(1 for x in ref if x < v), v
        assert (v in sl) == (v in ref), v

    # 3. Tower heights follow the geometric distribution we asked for:
    #    about half the nodes reach level 2, a quarter reach level 3.
    big = SkipList(range(50_000), seed=2)
    heights = big._tower_heights()
    for level, expected in ((2, 0.5), (3, 0.25), (4, 0.125)):
        share = sum(h >= level for h in heights) / len(heights)
        assert abs(share - expected) < 0.01, (level, share)

    # 4. Search cost grows like log n, not like n. Sixteen times the data
    #    should cost roughly four more comparisons per lookup, not 16x.
    def cost(n):
        s = SkipList(range(n), seed=3)
        s.comparisons = 0
        probes = 200
        for _ in range(probes):
            s.rank(rng.randrange(n))
        return s.comparisons / probes

    small, large = cost(2_000), cost(32_000)
    assert large - small < 12, (small, large)
    assert large < 3 * small, (small, large)

    print("all tests passed")
    print("  %d elements, %d distinct values" % (len(sl), len(set(ref))))
    print("  mean tower height: %.3f" % (sum(heights) / len(heights)))
    print("  comparisons per lookup: %.1f at n=2,000, %.1f at n=32,000"
          % (small, large))


if __name__ == "__main__":
    _test()
