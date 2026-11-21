# Alias Method

Vose's construction for sampling a discrete distribution in O(1) per draw,
built here over exact rational arithmetic so its central claim can be checked
rather than asserted.

## Run

    python3 alias.py

Standard library only. The script builds a table, verifies it, samples a million
draws from it, and compares its cost against binary search on a CDF.

## The claim

Any distribution over n outcomes is a *uniform* mixture of n two-outcome coins.
Scale every probability by n so the mean is exactly 1, then pair an outcome
sitting below 1 with one above it: the big one donates exactly what the small one
lacks, the small one's column is finished forever, and the big one goes back in
the pool with less mass. Each pairing retires one outcome, so n-1 of them finish
the table — and a draw is then `i = randrange(n)` followed by one comparison,
whatever n is.

`reconstruct()` reads the sampled distribution back off the columns, and under
`exact=True` it compares equal to the target as `Fraction`, with no tolerance.

## What was interesting

The leftover queue is where the floating-point version shows itself. When the
last pairing is done, every outcome still queued should be sitting at exactly 1,
and in exact arithmetic it is — residual 0. Every implementation of this
algorithm clamps those stragglers to 1 anyway, which quietly hides how far off
they were. Measuring the residual before clamping shows the error growing with
the chain of subtractions:

| n | residual |
| --- | --- |
| 100 | 4.4e-16 |
| 10,000 | 2.0e-11 |
| 1,000,000 | 5.5e-08 |

Each donation is `scaled[hi] -= 1 - scaled[lo]`, so a donor can be visited many
times and its error compounds along the way; the clamp absorbs the whole
accumulated drift into the last few columns. Harmless for sampling, but it means
the usual float build does not sample the distribution you handed it — it samples
one about 5e-8 away, and that gap is a property of n, not of the weights.

The cost comparison is the other half of the point: the CDF's binary search needs
log2(n) comparisons per draw (3.34, 9.97, 16.69 measured at n = 10, 1e3, 1e5),
while the alias table needs one at every size.
