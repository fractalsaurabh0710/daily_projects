# Bloom Filter

A Bloom filter written from scratch on the Python standard library: a
probabilistic set that answers membership with either "definitely not" or
"probably yes", and stores bits instead of keys.

## Run it

```
python3 bloom_filter.py
```

The file runs its own tests when executed directly. It fills a 10,000-item
filter, confirms there are zero false negatives, and measures the actual
false-positive rate against the 1% it was asked for.

## Usage

```python
bf = BloomFilter(capacity=10_000, error_rate=0.01)
bf.add("hello")
"hello" in bf    # True, always
"goodbye" in bf  # False, ~99% of the time
```

## The interesting bit

The error rate is designed rather than measured. Given the expected item
count `n` and a tolerable false-positive rate `p`, the optimal bit count and
number of hash functions are closed forms — `m = -n·ln(p)/(ln2)²` and
`k = (m/n)·ln2` — which for 1% works out to 9.59 bits and 7 hashes per item,
regardless of how big the keys are.

Two smaller details worth noting:

- **Seven hashes, one hash call.** Kirsch–Mitzenmacher says you can build `k`
  hash functions from two independent ones as `h1 + i·h2`. So the filter takes
  a single 128-bit BLAKE2b digest, splits it in half, and strides. Forcing
  `h2` odd keeps the stride from collapsing onto a short cycle.
- **Half the bits set is correct.** At optimal sizing a full filter has ~50% of
  its bits on, which is why `fill_ratio**num_hashes` predicts the current error
  rate so well — the test asserts the measured rate lands near it.
