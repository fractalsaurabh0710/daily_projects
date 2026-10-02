#!/usr/bin/env python3
"""hist - draw a horizontal histogram of numbers read from stdin.

Bin count is chosen by the Freedman-Diaconis rule unless -b is given:

    width = 2 * IQR / n**(1/3)

IQR scales with the spread of the middle half of the data, so unlike
Sturges' rule it does not get fooled by a couple of far-out values -
a single outlier widens the range but barely moves the IQR, so the
bins stay narrow enough to show the shape of the bulk.

Usage:
    seq 1 100 | python3 hist.py
    python3 hist.py -b 12 -w 50 < data.txt
"""

import argparse
import math
import re
import sys

NUMBER = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")
BLOCKS = " ▏▎▍▌▋▊▉█"  # eighths, for sub-character resolution


def read_numbers(stream):
    """Pull every number out of the input, ignoring any other text."""
    values = []
    for line in stream:
        values.extend(float(m.group()) for m in NUMBER.finditer(line))
    return values


def quantile(sorted_values, q):
    """Linear-interpolated quantile (the same convention numpy uses)."""
    if len(sorted_values) == 1:
        return sorted_values[0]
    pos = q * (len(sorted_values) - 1)
    lo = math.floor(pos)
    hi = math.ceil(pos)
    if lo == hi:
        return sorted_values[lo]
    return sorted_values[lo] + (sorted_values[hi] - sorted_values[lo]) * (pos - lo)


def freedman_diaconis_bins(values):
    """Bin count from the FD rule, clamped to something printable."""
    ordered = sorted(values)
    iqr = quantile(ordered, 0.75) - quantile(ordered, 0.25)
    span = ordered[-1] - ordered[0]
    if iqr <= 0 or span <= 0:
        return 1
    width = 2 * iqr / len(values) ** (1 / 3)
    return max(1, min(60, math.ceil(span / width)))


def bin_values(values, nbins):
    """Return (edges, counts). The last bin includes its right edge."""
    lo, hi = min(values), max(values)
    if hi == lo:
        hi = lo + 1.0
    step = (hi - lo) / nbins
    counts = [0] * nbins
    for v in values:
        idx = min(nbins - 1, int((v - lo) / step))
        counts[idx] += 1
    edges = [lo + i * step for i in range(nbins + 1)]
    return edges, counts


def bar(count, peak, width):
    """A bar of eighth-blocks, so small counts are still visible."""
    if count == 0 or peak == 0:
        return ""
    eighths = max(1, round(count / peak * width * 8))
    full, rest = divmod(eighths, 8)
    return "█" * full + (BLOCKS[rest] if rest else "")


def render(values, nbins, width):
    edges, counts = bin_values(values, nbins)
    peak = max(counts)
    label_w = max(len(f"{e:g}") for e in edges)
    count_w = len(str(peak))
    lines = []
    for i, count in enumerate(counts):
        left = f"{edges[i]:>{label_w}g}"
        right = f"{edges[i + 1]:<{label_w}g}"
        lines.append(f"{left} .. {right} | {count:>{count_w}} {bar(count, peak, width)}")
    mean = sum(values) / len(values)
    lines.append(
        f"\nn={len(values)}  min={min(values):g}  mean={mean:g}  "
        f"max={max(values):g}  bins={nbins}"
    )
    return "\n".join(lines)


def main(argv=None):
    p = argparse.ArgumentParser(description="Histogram of numbers from stdin.")
    p.add_argument("-b", "--bins", type=int, help="bin count (default: Freedman-Diaconis)")
    p.add_argument("-w", "--width", type=int, default=40, help="widest bar, in characters")
    args = p.parse_args(argv)

    values = read_numbers(sys.stdin)
    if not values:
        sys.exit("hist: no numbers found on stdin")
    nbins = args.bins or freedman_diaconis_bins(values)
    if nbins < 1:
        sys.exit("hist: --bins must be at least 1")
    print(render(values, nbins, max(1, args.width)))


if __name__ == "__main__":
    main()
