"""Cuckoo hashing, and the load factor where insertion stops terminating.

One table of `nb` buckets, each holding `b` keys, and two hash functions. A key
lives in one of its two buckets or nowhere at all, so a lookup touches at most
2b slots however full the table is -- there is no chain to walk and no
clustering to step through. Insertion pays for that: when both buckets are
full it evicts a resident at random and re-inserts it, which may evict another,
and so on. Above a load factor that depends only on b -- not on nb, not on the
hash functions -- that random walk stops terminating.

The eviction walk is a sequence of swaps, so it is exactly reversible: a failed
insert replays its trail backwards and leaves the table bit-for-bit as it was.
That costs nothing but time, which is what makes the threshold measurable
instead of destructive.

Run: python3 cuckoo.py
"""

import hashlib
import random
import struct

# Asymptotic thresholds for the random-walk insertion, from the literature.
KNOWN_THRESHOLD = {1: 0.500, 2: 0.897, 4: 0.977, 8: 0.998}


class CuckooTable:
    def __init__(self, n_buckets, bucket_size=1, max_kicks=500):
        self.nb = n_buckets
        self.b = bucket_size
        self.max_kicks = max_kicks
        self.slots = [[] for _ in range(n_buckets)]
        self.size = 0
        self.kicks = 0    # evictions performed, over the table's whole life
        self.probes = 0   # slots examined by lookup()

    @property
    def capacity(self):
        return self.nb * self.b

    @property
    def load(self):
        return self.size / self.capacity

    def _h(self, key, which):
        digest = hashlib.blake2b(
            repr(key).encode(), digest_size=8, key=b"cuckoo" + bytes([which])
        ).digest()
        return struct.unpack("<Q", digest)[0] % self.nb

    def _buckets(self, key):
        """The two homes of a key, nudged apart when both hashes agree.

        Without the nudge a 1-in-nb key has a single home, and at b=1 that one
        key alone would end the run -- the measurement would be of hash
        collisions rather than of the threshold.
        """
        i = self._h(key, 0)
        j = self._h(key, 1)
        return i, (j if j != i else (j + 1) % self.nb)

    def lookup(self, key):
        i, j = self._buckets(key)
        for bucket in (i, j):
            for resident in self.slots[bucket]:
                self.probes += 1
                if resident == key:
                    return True
        return False

    def insert(self, key):
        i, j = self._buckets(key)
        for bucket in (i, j):
            if len(self.slots[bucket]) < self.b:
                self.slots[bucket].append(key)
                self.size += 1
                return True

        cur, bucket, trail = key, random.choice((i, j)), []
        for _ in range(self.max_kicks):
            pos = random.randrange(self.b)
            trail.append((bucket, pos))
            cur, self.slots[bucket][pos] = self.slots[bucket][pos], cur
            self.kicks += 1
            a, c = self._buckets(cur)
            bucket = c if a == bucket else a         # the evictee's other home
            if len(self.slots[bucket]) < self.b:
                self.slots[bucket].append(cur)
                self.size += 1
                return True

        for bucket, pos in reversed(trail):          # unwind: table restored
            cur, self.slots[bucket][pos] = self.slots[bucket][pos], cur
        return False


def snapshot(table):
    return tuple(tuple(bucket) for bucket in table.slots)


def fill_to_failure(bucket_size, capacity=4096, seed=0):
    """Insert distinct keys until one insert fails. Returns (load, table, keys)."""
    random.seed(seed)
    table = CuckooTable(capacity // bucket_size, bucket_size)
    keys, n = [], 0
    while True:
        key = f"key-{seed}-{n}"
        n += 1
        before = snapshot(table)
        if not table.insert(key):
            assert snapshot(table) == before, "failed insert must leave the table alone"
            return table.load, table, keys
        keys.append(key)


def main():
    print("Cuckoo hashing: where the eviction walk stops terminating")
    print("capacity 4096 slots, max_kicks 500, 20 trials per bucket size\n")
    print(f"{'b':>2}  {'buckets':>8}  {'measured load':>14}  {'asymptotic':>11}")
    for b in (1, 2, 4, 8):
        loads = [fill_to_failure(b, seed=s)[0] for s in range(20)]
        mean = sum(loads) / len(loads)
        print(f"{b:>2}  {4096 // b:>8}  {mean:>13.3f}   {KNOWN_THRESHOLD[b]:>10.3f}")

    print("\nLookup is bounded by 2b slots at every load (b=4, so never past 8):")
    _, table, keys = fill_to_failure(4, seed=0)
    full_load = table.load
    for fraction in (0.25, 0.50, 1.00):
        sub = keys[: int(len(keys) * fraction)]
        random.seed(1)
        probe = CuckooTable(1024, 4)
        for key in sub:
            probe.insert(key)
        hits = probe.probes = 0
        for key in sub:
            hits += probe.lookup(key)
        per_hit = probe.probes / len(sub)
        probe.probes = 0
        misses = sum(probe.lookup(f"absent-{i}") for i in range(len(sub)))
        per_miss = probe.probes / len(sub)
        assert hits == len(sub) and misses == 0
        print(
            f"  load {probe.load:.2f}: {per_hit:4.2f} probes per hit, "
            f"{per_miss:4.2f} per miss"
        )

    print("\nInsertion cost is where the load goes (b=4, evictions per insert):")
    random.seed(2)
    table = CuckooTable(1024, 4)
    bands, n, last = [(0.0, 0.5), (0.5, 0.9), (0.9, 0.95), (0.95, 1.0)], 0, 0
    totals = {band: [0, 0] for band in bands}
    while True:
        band = next((x for x in bands if x[0] <= table.load < x[1]), None)
        before = table.kicks
        if not table.insert(f"k{n}"):
            break
        n += 1
        if band:
            totals[band][0] += table.kicks - before
            totals[band][1] += 1
    for low, high in bands:
        kicks, inserts = totals[(low, high)]
        if inserts:
            print(f"  load {low:.2f}-{high:.2f}: {kicks / inserts:7.2f} evictions per insert")
    print(f"\nFilled to {table.load:.3f} before the walk gave up "
          f"(single run; the 20-trial mean above was {full_load:.3f} at b=4).")
    print("The average climbs as buckets fill, but 2b is the ceiling: a lookup at")
    print("load 0.999 is the same eight slots as a lookup at load 0.5.")


if __name__ == "__main__":
    main()
