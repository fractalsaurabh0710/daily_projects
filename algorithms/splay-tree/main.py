"""Splay tree: a binary search tree that stores no balance information at all.

No colours, no heights, no ranks. Every access rotates the node it touched up to
the root, and that single rule is enough for O(log n) amortised operations. The
payoff is the part a balanced tree cannot match: on a skewed workload the hot
keys drift to the top and the average access gets *cheaper than log n*. The demo
at the bottom measures that against the Shannon entropy of the access
distribution, which is the bound the static-optimality theorem promises.
"""

import math
import random


class Node:
    __slots__ = ("key", "value", "left", "right")

    def __init__(self, key=None, value=None):
        self.key = key
        self.value = value
        self.left = None
        self.right = None


def splay(root, key):
    """Top-down splay. Returns the new root: `key` if present, else its
    closest neighbour. Iterative on purpose -- a splay tree is allowed to be a
    10,000-node path, and recursion would die on it."""
    if root is None:
        return None
    header = Node()
    left = right = header      # accumulate the < key and > key spines
    t = root
    while True:
        if key < t.key:
            if t.left is None:
                break
            if key < t.left.key:
                y = t.left             # zig-zig: rotate right first
                t.left = y.right
                y.right = t
                t = y
                if t.left is None:
                    break
            right.left = t             # link t onto the > key spine
            right = t
            t = t.left
        elif key > t.key:
            if t.right is None:
                break
            if key > t.right.key:
                y = t.right            # zag-zag: rotate left first
                t.right = y.left
                y.left = t
                t = y
                if t.right is None:
                    break
            left.right = t
            left = t
            t = t.right
        else:
            break
    left.right = t.left                # reassemble around the new root
    right.left = t.right
    t.left = header.right
    t.right = header.left
    return t


class SplayTree:
    def __init__(self):
        self.root = None
        self.size = 0
        self.probes = 0                # nodes compared, across all accesses

    def _probe_depth(self, key):
        """Comparisons a plain BST search would make on the tree as it stands."""
        n, d = self.root, 0
        while n is not None:
            d += 1
            if key < n.key:
                n = n.left
            elif key > n.key:
                n = n.right
            else:
                break
        return d

    def get(self, key, default=None):
        if self.root is None:
            return default
        self.probes += self._probe_depth(key)
        self.root = splay(self.root, key)
        return self.root.value if self.root.key == key else default

    def put(self, key, value):
        if self.root is None:
            self.root = Node(key, value)
            self.size = 1
            return
        self.probes += self._probe_depth(key)
        self.root = splay(self.root, key)
        if self.root.key == key:
            self.root.value = value
            return
        n = Node(key, value)
        if key < self.root.key:          # split the old root under the new one
            n.right = self.root
            n.left = self.root.left
            self.root.left = None
        else:
            n.left = self.root
            n.right = self.root.right
            self.root.right = None
        self.root = n
        self.size += 1

    def pop(self, key, default=None):
        if self.root is None:
            return default
        self.root = splay(self.root, key)
        if self.root.key != key:
            return default
        gone, left, right = self.root, self.root.left, self.root.right
        if left is None:
            self.root = right
        else:
            self.root = splay(left, key)   # key beats everything here -> max
            self.root.right = right
        self.size -= 1
        return gone.value

    def __contains__(self, key):
        return self.get(key, _MISS) is not _MISS

    def __len__(self):
        return self.size

    def keys(self):
        out, stack, n = [], [], self.root
        while stack or n:
            while n:
                stack.append(n)
                n = n.left
            n = stack.pop()
            out.append(n.key)
            n = n.right
        return out


_MISS = object()


def _test_correctness():
    random.seed(7)
    tree, ref = SplayTree(), {}
    for _ in range(4000):
        k = random.randrange(500)
        roll = random.random()
        if roll < 0.55:
            tree.put(k, k * k)
            ref[k] = k * k
        elif roll < 0.8:
            assert tree.get(k, _MISS) == ref.get(k, _MISS), k
        else:
            assert tree.pop(k, _MISS) == ref.pop(k, _MISS), k
        assert len(tree) == len(ref)
    assert tree.keys() == sorted(ref)            # still a search tree
    assert all(tree.get(k) == v for k, v in ref.items())
    print(f"correctness: {len(ref)} live keys, in-order and values match a dict")


def _test_static_optimality():
    """Splay cost should track the entropy of the access distribution, not log n."""
    random.seed(11)
    n = 2048
    tree = SplayTree()
    for k in range(n):
        tree.put(k, None)

    hot = random.sample(range(n), 40)            # 2% of the keys, 90% of the hits
    workload = [random.choice(hot) if random.random() < 0.9 else random.randrange(n)
                for _ in range(60_000)]

    counts = {}
    for k in workload:
        counts[k] = counts.get(k, 0) + 1
    entropy = -sum((c / len(workload)) * math.log2(c / len(workload))
                   for c in counts.values())

    tree.probes = 0
    for k in workload:
        tree.get(k)
    avg = tree.probes / len(workload)
    balanced = math.log2(n) - 1                  # avg depth of a perfect BST

    print(f"static optimality: {avg:.2f} probes/access vs {balanced:.2f} for a "
          f"perfectly balanced tree (entropy of the workload: {entropy:.2f} bits)")
    assert avg < balanced, (avg, balanced)
    assert avg < 4 * entropy + 2, (avg, entropy)


def _test_sequential_is_constant():
    """Walking the keys in order costs the same per access whatever n is.

    Inserting 1..n ascending leaves the tree as a long path, so a plain BST
    would pay O(n) for the first lookup. Splaying makes an in-order scan flat:
    the per-access cost stops growing while log n keeps climbing."""
    costs = {}
    for n in (5_000, 20_000, 80_000):
        tree = SplayTree()
        for k in range(n):
            tree.put(k, None)
        tree.probes = 0
        for k in range(n):
            tree.get(k)
        costs[n] = tree.probes / n
        print(f"sequential scan: n={n:>6}  {costs[n]:.2f} probes/access "
              f"(a balanced tree would pay {math.log2(n) - 1:.1f})")
    # cost is flat in n, so a 16x bigger tree must not cost 16x -- or even 1.5x
    assert costs[80_000] < 1.5 * costs[5_000], costs
    assert costs[80_000] < 8, costs


if __name__ == "__main__":
    _test_correctness()
    _test_static_optimality()
    _test_sequential_is_constant()
    print("all tests passed")
