# entropy-map

Draws a per-block Shannon entropy map of a file, so you can see where the
structured parts end and the compressed, encrypted or packed parts begin.
Pure standard library.

```
$ python3 entropy_map.py mix.bin --block 512
mix.bin  14143 bytes  block=512B  random reads as 7.59 bits at this size

  0x00000000  ████████████████▌              4.47/7.59  structured
  0x00000200  ████████████████               4.35/7.59  structured
  0x00000400  ███████████████▌               4.21/7.59  structured
  0x00000600  █████████████████▍             4.72/7.59  structured
  0x00000800  ███████████████████████████▍   7.43/7.59  random
  0x00000a00  ███████████████████████████▉   7.55/7.59  random
  ...
  near-random regions (compressed, encrypted or packed):
    0x00000800 .. 0x0000373f   12095 bytes
```

## Running it

```
python3 entropy_map.py FILE [--block N] [--rows N] [--no-color]
python3 entropy_map.py --selftest
```

With no `--block`, the block size is the smallest power of two that fits the
file in `--rows` rows (default 32). `--selftest` needs no input file: it
checks the prediction below against measured random data, checks that the
three classification bands fire on flat, textual and random blocks, and
checks that a 4 KiB random region buried between two dull ones is found at
exactly the right offsets.

## The one interesting thing

Normalising against `log2(256) = 8` bits is wrong, and not by a little. A
256-byte block of perfectly random bytes measures **7.18 bits**, because 256
draws land on only about 162 of the 256 possible values and the plug-in
estimator reads the 94 missing ones as structure. Score against 8 bits and
genuinely random data looks 10% structured; score against the right ceiling
and it pins the bar.

The textbook fix, Miller–Madow, subtracts `(K-1) / (2n ln 2)` bits for the
`K` symbols you expect to see. It is also wrong here — it predicts 7.55 at
n=256 — because it assumes every symbol shows up often enough for the
first-order term to dominate, and at one expected hit per symbol it does
not. So the ceiling is computed exactly instead. Byte counts are
multinomial and all 256 symbols are interchangeable, which collapses the
expectation to a single binomial sum:

```
E[H] = -256 * Σ_j  P(c = j) · (j/n) · log2(j/n),    c ~ Bin(n, 1/256)
```

cheap to evaluate because `P(c = j)` dies off a few sigma above `n/256`.
`--selftest` prints all three numbers side by side, and the exact column
tracks the measurement to within 0.01 bits at every size while Miller–Madow
is off by 0.37 at the small end:

```
  n=   256  exact 7.175  measured 7.178  (miller-madow 7.546)
  n=   512  exact 7.590  measured 7.582  (miller-madow 7.689)
  n=  1024  exact 7.809  measured 7.814  (miller-madow 7.824)
  n=  4096  exact 7.955  measured 7.955  (miller-madow 7.955)
  n= 16384  exact 7.989  measured 7.988  (miller-madow 7.989)
```

Which is the practical argument for small blocks being useful at all: a
512-byte window can still call a region random, as long as you know that
random means 7.59 there.
