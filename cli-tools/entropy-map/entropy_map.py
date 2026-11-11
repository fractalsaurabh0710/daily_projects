#!/usr/bin/env python3
"""entropy-map - draw a per-block Shannon entropy map of a file.

Finite-sample bias is the whole point. A 256-byte block of perfectly random
bytes measures 7.18 bits, not 8.00: 256 draws land on only ~162 of the 256
possible values, and the plug-in estimator reads the gaps as structure. So
the bars here are normalised against the *expected* entropy of random data
at this block size, computed exactly, not against log2(256). A full bar
means "indistinguishable from random", which is a claim you can make.

Usage:  python3 entropy_map.py FILE [--block N] [--rows N] [--no-color]
        python3 entropy_map.py --selftest
"""

import argparse
import math
import os
import random
import sys
from collections import Counter
from functools import lru_cache

EIGHTHS = " ▏▎▍▌▋▊▉█"
RESET = "\033[0m"
BANDS = [  # (upper bound on normalised entropy, colour, label)
    (0.30, "\033[34m", "flat"),
    (0.70, "\033[36m", "structured"),
    (0.92, "\033[33m", "mixed"),
    (9.99, "\033[31m", "random"),
]
BAR_WIDTH = 28
LN2 = math.log(2.0)


def entropy_bits(buf):
    """Plug-in (maximum-likelihood) Shannon entropy of a byte string."""
    n = len(buf)
    if n == 0:
        return 0.0
    h = -sum((c / n) * math.log2(c / n) for c in Counter(buf).values())
    return max(0.0, h)  # a single-valued block gives -0.0; don't print that


@lru_cache(maxsize=None)
def expected_ceiling(n, alphabet=256):
    """Exact expected plug-in entropy of n uniform draws over `alphabet`.

    Counts are multinomial and every symbol is interchangeable, so the
    expectation collapses to one binomial sum:

        E[H] = -K * sum_j P(c = j) * (j/n) * log2(j/n),   c ~ Bin(n, 1/K)

    which is cheap because P(c = j) dies off a few sigma above the mean.
    The textbook shortcut (Miller-Madow, see below) is not good enough
    here: at n = 256 it predicts 7.55 bits where the truth is 7.18.
    """
    if n <= 1:
        return 0.0
    p = 1.0 / alphabet
    lam = n * p
    hi = min(n, int(lam + 12.0 * math.sqrt(lam) + 48))
    log_p, log_q = math.log(p), math.log1p(-p)
    log_n_fact = math.lgamma(n + 1)
    total = 0.0
    for j in range(1, hi + 1):
        log_pmf = (log_n_fact - math.lgamma(j + 1) - math.lgamma(n - j + 1)
                   + j * log_p + (n - j) * log_q)
        total += math.exp(log_pmf) * (j / n) * math.log2(j / n)
    return -alphabet * total


def miller_madow(n, alphabet=256):
    """The usual first-order correction, kept only for comparison.

    It subtracts (K - 1) / (2 n ln 2) bits from log2(K), with K the number
    of symbols expected to be *seen*. That is a good correction once every
    symbol shows up several times, and badly optimistic before then.
    """
    if n <= 1:
        return 0.0
    seen = alphabet * (1.0 - (1.0 - 1.0 / alphabet) ** n)
    return min(math.log2(min(n, alphabet)),
               math.log2(alphabet) - (seen - 1.0) / (2.0 * n * math.log(2.0)))


def band(norm):
    for upper, colour, label in BANDS:
        if norm < upper:
            return colour, label
    return BANDS[-1][1], BANDS[-1][2]


def bar(norm, width=BAR_WIDTH):
    cells = max(0.0, min(1.0, norm)) * width
    full = int(cells)
    rest = int(round((cells - full) * 8))
    if rest == 8:
        full, rest = full + 1, 0
    return ("█" * full + (EIGHTHS[rest] if rest else "")).ljust(width)


def choose_block(size, rows, floor=256):
    """Smallest power-of-two block >= floor that fits the file in `rows`."""
    block = floor
    while size / block > rows:
        block *= 2
    return block


def scan(data, block):
    out = []
    for off in range(0, len(data), block):
        chunk = data[off:off + block]
        h = entropy_bits(chunk)
        ceil = expected_ceiling(len(chunk))
        out.append((off, len(chunk), h, ceil, h / ceil if ceil > 0 else 0.0))
    return out


def regions(rows, threshold=0.92):
    """Contiguous runs of near-random blocks, as (start, end) byte offsets."""
    runs, start = [], None
    for off, length, _h, _c, norm in rows:
        if norm >= threshold and start is None:
            start = off
        elif norm < threshold and start is not None:
            runs.append((start, off))
            start = None
        last_end = off + length
    if start is not None:
        runs.append((start, last_end))
    return runs


def render(path, data, block, colour):
    rows = scan(data, block)
    print(f"{path}  {len(data)} bytes  block={block}B  "
          f"random reads as {expected_ceiling(block):.2f} bits at this size")
    print()
    for off, length, h, ceil, norm in rows:
        col, label = band(norm)
        on, off_ = (col, RESET) if colour else ("", "")
        print(f"  {off:#010x}  {on}{bar(norm)}{off_}  "
              f"{h:5.2f}/{ceil:.2f}  {label}"
              + ("" if length == block else f"  ({length}B)"))
    print()
    found = regions(rows)
    if found:
        print("  near-random regions (compressed, encrypted or packed):")
        for a, b in found:
            print(f"    {a:#010x} .. {b:#010x}   {b - a} bytes")
    else:
        print("  no near-random regions")


def selftest():
    rnd = random.Random(20261111)

    # 1. The ceiling is a prediction, so check it against real random data.
    print("entropy of random blocks: exact prediction vs. measurement")
    print("  (Miller-Madow shown for comparison; it is the one that misses)")
    for n in (256, 512, 1024, 4096, 16384):
        trials = [entropy_bits(bytes(rnd.randrange(256) for _ in range(n)))
                  for _ in range(24)]
        measured = sum(trials) / len(trials)
        exact = expected_ceiling(n)
        print(f"  n={n:6d}  exact {exact:.3f}  measured {measured:.3f}"
              f"  (miller-madow {miller_madow(n):.3f})")
        assert abs(measured - exact) < 0.03, (n, exact, measured)
    assert expected_ceiling(256) < 7.25, "256 random bytes do not reach 8 bits"

    # 2. Classification of three kinds of block.
    words = b"the quick brown fox jumps over a lazy dog while it rains "
    cases = [
        (bytes(1024), "flat"),
        ((words * 32)[:1024], "structured"),
        (bytes(rnd.randrange(256) for _ in range(1024)), "random"),
    ]
    print("\nclassification:")
    for payload, want in cases:
        h = entropy_bits(payload)
        norm = h / expected_ceiling(len(payload))
        _col, got = band(norm)
        print(f"  {want:<11} -> {got:<11} ({h:.2f} bits, normalised {norm:.2f})")
        assert got == want, (want, got)

    # 3. A region hidden in the middle of an otherwise dull file.
    payload = ((words * 80)[:4096]
               + bytes(rnd.randrange(256) for _ in range(4096))
               + bytes(4096))
    found = regions(scan(payload, 1024))
    print(f"\nembedded random region found at {found}")
    assert found == [(4096, 8192)], found

    print("\nall checks passed")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("file", nargs="?", help="file to map")
    ap.add_argument("--block", type=int, default=0,
                    help="block size in bytes (default: fit --rows)")
    ap.add_argument("--rows", type=int, default=32,
                    help="target number of rows when --block is unset")
    ap.add_argument("--no-color", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        return 0
    if not args.file:
        ap.error("give a file, or --selftest")

    with open(args.file, "rb") as fh:
        data = fh.read()
    if not data:
        print("empty file")
        return 1
    block = args.block or choose_block(len(data), max(1, args.rows))
    if block < 32:
        ap.error("block size below 32 bytes measures almost nothing")
    render(args.file, data, block, colour=not args.no_color and sys.stdout.isatty())
    return 0


if __name__ == "__main__":
    sys.exit(main())
