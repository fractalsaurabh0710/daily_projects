# Cuckoo Hashing

One table of buckets, two hash functions, and a rule: a key lives in one of its
two buckets or nowhere. There is no chain to walk and no probe sequence to
follow, so a lookup examines at most `2b` slots — eight, for buckets of four —
no matter how full the table is.

Insertion is what pays for that. When both of a key's buckets are full it evicts
a resident at random and re-inserts it into the evictee's *other* bucket, which
may evict another, and so on. Above a load factor that depends only on the
bucket size, that random walk stops terminating.

## Run

    python3 cuckoo.py

Standard library only.

## What it measures

Filling a 4096-slot table until the first insertion failure, 20 trials each:

| b | measured load | asymptotic |
| - | ------------- | ---------- |
| 1 | 0.518 | 0.500 |
| 2 | 0.883 | 0.897 |
| 4 | 0.970 | 0.977 |
| 8 | 0.994 | 0.998 |

The threshold is a property of `b` alone — not of the table size, not of the
hash functions. At `b=1` the measurement lands slightly *above* the asymptote
and at larger `b` slightly below: 4096 slots is small enough for finite-size
effects to go in both directions.

The cost does not vanish, it moves into insertion. Evictions per insert at
`b=4`, by load band: 0.00 below 0.5, 0.79 up to 0.9, 10.33 from 0.9 to 0.95,
and 51.20 past 0.95. The curve going vertical *is* the threshold.

## The one interesting thing

The eviction walk is a sequence of swaps, so it is exactly reversible. When the
walk exhausts its kick budget, replaying the trail backwards leaves the table
bit-for-bit as it was — the code asserts this on every failure, by comparing
snapshots. A failed insert costs time and nothing else.

That is what makes the threshold measurable rather than destructive: a real
implementation responds to failure by rehashing into a larger table, which
destroys the evidence. Here the table survives its own failure, so the run can
report the exact load at which the walk gave up.

A second detail: when both hashes agree, the second bucket is nudged one
along. Without it a 1-in-`nb` key has a single home, and at `b=1` that one key
would end the run on its own — the measurement would be of hash collisions
rather than of the threshold.
