# Dict Collisions

CPython's dict insertion path, reimplemented in pure Python, used to predict
exactly how many times a real dict will call `__eq__` while being filled.

```
python3 collisions.py
```

The tests compare the simulation against the interpreter running it, across
workloads with one shared hash, distinct hashes, keys that start in the same slot
with different hashes, and buckets of various shapes. Every case has to match to
the comparison, not approximately.

## What is modelled

- the probe sequence `i = (i*5 + perturb + 1) & mask` with `perturb >>= 5`
- stored-hash comparison before `__eq__`, which makes slot collisions between
  unequal hashes free
- the two-thirds load factor and the grow-to-`used * 3` rule, rounded up to a
  power of two with a floor of 8
- resize happening after lookup and before placement, and reinserting by hash
  alone, so it costs no comparisons
- `__hash__` returning -1 being stored as -2, since C reserves -1 for errors

## The interesting part

The obvious cost for n keys sharing a hash is n(n-1)/2, one comparison against
each key already in the table. Whether that is correct turns out to depend on the
hash *value*. `perturb` starts as the hash and is shifted right 5 bits per step,
and while it is nonzero the walk can come back to a slot it has already probed and
compare the same key a second time. For any hash below 32 the term is gone before
the first step, which leaves `i = (5i+1) mod 2**k` — a full-period permutation that
cannot revisit anything — so those hashes land on n(n-1)/2 exactly. 100 keys
hashing to 31 cost 4950 comparisons; 100 hashing to 32 cost 4994.

The probe table at the end of the run shows the mechanism directly: hashes 5, 69,
133 and 1048581 all start in slot 5 of a 64-slot table, because `& mask` only sees
their low bits, and all leave by different routes, because the next step shifts in
the bits the mask discarded. Hash 133 is the one that revisits slot 5 on its fifth
probe.

The simulation encodes one interpreter's policy constants, which have changed
before, so the tests are the version check: if a future CPython alters the growth
rule or the shift, they fail with both numbers printed rather than quietly
drifting. Checked against 3.10.
