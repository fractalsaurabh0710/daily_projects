#!/usr/bin/env python3
"""Tests for hist.py. Run: python3 test_hist.py"""

import io
import hist

# Numbers are scraped out of arbitrary text, including negatives and exponents.
assert hist.read_numbers(io.StringIO("cpu 12.5%\nmem -3 1e2 x\n")) == [12.5, -3.0, 100.0]

# Quantiles match numpy's linear interpolation.
ordered = [1, 2, 3, 4]
assert hist.quantile(ordered, 0.25) == 1.75
assert hist.quantile(ordered, 0.75) == 3.25
assert hist.quantile([7], 0.5) == 7

# Every value lands in exactly one bin, including the maximum.
edges, counts = hist.bin_values([0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5)
assert sum(counts) == 11
assert counts == [2, 2, 2, 2, 3], counts
assert edges[0] == 0 and edges[-1] == 10

# A degenerate range still produces one usable bin.
edges, counts = hist.bin_values([5, 5, 5], 1)
assert counts == [3] and edges == [5, 6.0]
assert hist.freedman_diaconis_bins([5, 5, 5]) == 1

# A lone outlier must not blow the bin width up: FD keeps resolution on the bulk.
bulk = [i / 10 for i in range(1000)]
assert hist.freedman_diaconis_bins(bulk) > 5
assert hist.freedman_diaconis_bins(bulk + [1e6]) > 5

# Bars: a nonzero count is never rendered as empty, and the peak fills the width.
assert hist.bar(1, 10_000, 40) == "▏"
assert hist.bar(0, 10, 40) == ""
assert hist.bar(10, 10, 40) == "█" * 40

out = hist.render([1, 2, 2, 3], 3, 10)
assert "n=4" in out and "mean=2" in out and "bins=3" in out

print("all tests passed")
