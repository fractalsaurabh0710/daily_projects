"""Predicting, to the comparison, how many __eq__ calls a dict will make.

"A bad __hash__ makes dicts slow" is usually left there. It can be made exact:
reimplement CPython's open addressing in pure Python -- the probe sequence, the
two-thirds load factor, the grow-to-used*3 rule -- and the simulation says how
many times a real dict will call __eq__ before it has finished inserting a given
list of hashes. Not approximately. The same integer, for every workload below.

The simulation is also the only honest way to get the number. The obvious guess
for n keys sharing one hash is n(n-1)/2 -- one comparison per key already in the
table -- and whether that is right depends on the hash value, which is a strange
enough result to be worth the simulation on its own. The probe sequence carries a
`perturb` term seeded with the hash and shifted right 5 bits per step; while it is
nonzero the walk can revisit a slot it has already looked at, comparing the same
key twice on the way past. For a hash below 32 the term is gone before the first
step, leaving i = (5i+1) mod 2**k, a full-period permutation that cannot repeat --
so those hashes hit the naive formula exactly and anything larger tends to run
over it. 100 keys hashing to 31 cost 4950 comparisons; 100 hashing to 32 cost
4994.

Run this file to check the simulation against the interpreter running it.
"""

from time import perf_counter

MINSIZE = 8  # PyDict_MINSIZE
PERTURB_SHIFT = 5

EQ_CALLS = 0


class Key:
    """A key whose hash is whatever you say it is, and whose __eq__ is counted."""

    __slots__ = ("label", "h")

    def __init__(self, label, h):
        self.label = label
        self.h = h

    def __hash__(self):
        return self.h

    def __eq__(self, other):
        global EQ_CALLS
        EQ_CALLS += 1
        # Labels are unique, so no insertion is ever a replacement: every key
        # below really does take a slot of its own.
        return self.label == other.label


def real_dict(hashes):
    """Fill a dict with one key per hash; return (__eq__ calls, seconds)."""
    global EQ_CALLS
    keys = [Key(i, h) for i, h in enumerate(hashes)]
    EQ_CALLS = 0
    start = perf_counter()
    d = {}
    for k in keys:
        d[k] = k.label
    elapsed = perf_counter() - start
    assert len(d) == len(keys), "keys collapsed; __eq__ is lying"
    return EQ_CALLS, elapsed


def effective_hash(h):
    """What the interpreter actually stores for a __hash__ returning h.

    CPython reserves -1 as the error signal from tp_hash, so an object whose
    __hash__ returns -1 is hashed as -2. Miss this and the simulation is wrong
    for exactly one input value out of 2**64.
    """
    return -2 if h == -1 else h


def probe(h, mask):
    """CPython's probe sequence (Objects/dictobject.c), as an endless walk.

    The first slot uses only the low bits of the hash. Every slot after it mixes
    in bits that `& mask` threw away, so two hashes landing in the same slot
    still leave it by different routes.
    """
    i = h & mask
    perturb = h & ((1 << 64) - 1)  # the C unsigned, so the shift terminates
    yield i
    while True:
        perturb >>= PERTURB_SHIFT
        i = (i * 5 + perturb + 1) & mask
        yield i


class DictSim:
    """CPython's dict insertion path, counting the comparisons it would cost."""

    def __init__(self):
        self.slots = []  # one entry per slot: (label, hash) or None
        self.mask = -1
        self.usable = 0  # dk_usable: inserts left before the table must grow
        self.used = 0
        self.comparisons = 0

    def insert(self, label, h):
        if not self.slots:
            self._alloc(MINSIZE)

        # Lookup. Stored hashes are compared first, so a slot collision between
        # unequal hashes never reaches __eq__.
        for s in probe(h, self.mask):
            entry = self.slots[s]
            if entry is None:
                break  # DKIX_EMPTY: the key is not here
            if entry[1] == h:
                self.comparisons += 1  # __eq__, which returns False

        # The table grows before the new key is placed, never during lookup.
        if self.usable <= 0:
            self._grow()

        for s in probe(h, self.mask):
            if self.slots[s] is None:
                self.slots[s] = (label, h)
                break
        self.usable -= 1
        self.used += 1

    def _alloc(self, size):
        self.slots = [None] * size
        self.mask = size - 1
        self.usable = size * 2 // 3 - self.used  # USABLE_FRACTION

    def _grow(self):
        size = MINSIZE
        while size < self.used * 3:  # GROWTH_RATE
            size <<= 1
        old = [e for e in self.slots if e is not None]
        self._alloc(size)
        for entry in old:  # reinserted by hash alone: no comparisons
            for s in probe(entry[1], self.mask):
                if self.slots[s] is None:
                    self.slots[s] = entry
                    break


def predict(hashes):
    sim = DictSim()
    for label, h in enumerate(hashes):
        sim.insert(label, effective_hash(h))
    return sim.comparisons


def test():
    workloads = {
        "one hash, n=1..12": [[0xBAD] * n for n in range(1, 13)],
        "one hash, larger": [[0xBAD] * n for n in (50, 100, 300, 777)],
        "hash value irrelevant": [[h] * 60 for h in (0, 1, -1, 7, 1 << 40)],
        "distinct hashes": [list(range(5000))],
        "same slot, different hash": [[i * 64 for i in range(2000)]],
        "40 buckets of 25": [[i // 25 for i in range(1000)]],
        "lopsided buckets": [[min(i, 9) for i in range(400)]],
        "hash 32, just past the shift": [[32] * 200, [33] * 200],
    }
    for name, cases in workloads.items():
        for hashes in cases:
            got, _ = real_dict(hashes)
            want = predict(hashes)
            assert got == want, f"{name}: dict said {got}, simulation said {want}"
    # A hash below 32 loses its perturb term before the first step, so its walk
    # is the pure permutation and no key is ever compared against twice.
    for h in range(32):
        assert predict([h] * 200) == 200 * 199 // 2, h
    assert predict([32] * 200) > 200 * 199 // 2

    print("all tests passed")


def report():
    print("\nn keys sharing one hash, comparisons to insert them all:")
    print("    n     n(n-1)/2   hash 0: real / predicted   hash 0xBAD: real / predicted")
    for n in (10, 100, 1000, 4000):
        guess = n * (n - 1) // 2
        zero, _ = real_dict([0] * n)
        bad, _ = real_dict([0xBAD] * n)
        print(f"{n:>5}  {guess:>11,}   {zero:>11,} / {predict([0] * n):<11,}"
              f"  {bad:>11,} / {predict([0xBAD] * n):<11,}")
    print("  Hashes below 32 match the naive formula exactly; 0xBAD, like most")
    print("  larger values, runs over it.")

    n = 4000
    _, slow = real_dict([0xBAD] * n)
    _, fast = real_dict(range(n))
    print(f"\n{n} keys: one hash {slow:.4f}s, distinct hashes {fast:.4f}s"
          f" ({slow / fast:.0f}x)")

    print("\nprobe sequence in a 64-slot table:")
    for h in (5, 5 + 64, 5 + 128, 5 + (1 << 20)):
        walk = [s for s, _ in zip(probe(h, 63), range(7))]
        print(f"  hash {h:>9}   {' -> '.join(f'{s:>2}' for s in walk)}")
    print("  Same first slot every time, and never the same second: the high bits")
    print("  `& mask` discarded come back on the next probe. Hash 133 is the")
    print("  revisit -- its fifth probe is slot 5 again, where it has already")
    print("  compared a key, and that is the excess in the table above.")


if __name__ == "__main__":
    test()
    report()
