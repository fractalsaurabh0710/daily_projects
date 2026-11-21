"""Vose's alias method: O(1) sampling from any discrete distribution.

The construction rests on a claim that is not obvious: any distribution over n
outcomes is a *uniform* mixture of n two-outcome coins.  Scale every probability
by n so the mean is exactly 1, then repeatedly pair an outcome below 1 with one
above it -- the big one donates whatever the small one lacks and stays in the
pool.  Each pairing permanently fills one column and removes one outcome, so n-1
pairings suffice, and a draw afterwards is one randrange plus one comparison no
matter how large n is.

Run: python3 alias.py
"""

from collections import Counter
from fractions import Fraction
import random


class AliasTable:
    """Column i yields outcome i with probability prob[i], else alias[i].

    With exact=True the construction runs over Fraction, so the reconstructed
    distribution is bit-for-bit the target one and the leftover residual is 0.
    """

    def __init__(self, weights, exact=False):
        n = self.n = len(weights)
        one = Fraction(1) if exact else 1.0
        total = sum(weights)
        if exact:
            scaled = [Fraction(w) * n / Fraction(total) for w in weights]
        else:
            scaled = [w * n / total for w in weights]

        small = [i for i in range(n) if scaled[i] < one]
        large = [i for i in range(n) if scaled[i] >= one]
        self.prob = [one] * n
        self.alias = list(range(n))
        self.pairings = 0

        while small and large:
            lo, hi = small.pop(), large.pop()
            self.prob[lo] = scaled[lo]
            self.alias[lo] = hi
            # the donor keeps only what it did not give away
            scaled[hi] = scaled[hi] - (one - scaled[lo])
            (small if scaled[hi] < one else large).append(hi)
            self.pairings += 1

        # anything still queued should be sitting at exactly 1
        self.residual = max((abs(float(scaled[i] - one)) for i in small + large),
                            default=0.0)
        for i in small + large:
            self.prob[i], self.alias[i] = one, i

    def sample(self, rng):
        i = rng.randrange(self.n)
        return i if rng.random() < self.prob[i] else self.alias[i]

    def reconstruct(self):
        """The distribution the table actually samples, read off its columns."""
        mass = [Fraction(0)] * self.n
        share = Fraction(1, self.n)
        for i in range(self.n):
            p = Fraction(self.prob[i])
            mass[i] += share * p
            mass[self.alias[i]] += share * (1 - p)
        return mass


def cdf_probes(cdf, x):
    """Binary search on a cumulative table, counting comparisons."""
    lo, hi, probes = 0, len(cdf) - 1, 0
    while lo < hi:
        mid = (lo + hi) // 2
        probes += 1
        if x <= cdf[mid]:
            hi = mid
        else:
            lo = mid + 1
    return lo, probes


def chi_square(counts, weights, draws):
    total = sum(weights)
    stat = 0.0
    for k, w in enumerate(weights):
        expected = draws * w / total
        stat += (counts[k] - expected) ** 2 / expected
    return stat


if __name__ == "__main__":
    # 1. exact arithmetic reproduces the target distribution with no residual
    weights = [1, 1, 1, 97, 300, 2, 598]
    table = AliasTable(weights, exact=True)
    target = [Fraction(w, sum(weights)) for w in weights]
    assert table.reconstruct() == target, table.reconstruct()
    assert table.residual == 0.0
    assert table.pairings == len(weights) - 1, table.pairings
    print(f"exact build: {len(weights)} outcomes, {table.pairings} pairings, "
          f"residual {table.residual}, reconstruction exact")

    # 2. the coins really do sample the distribution.  The weights are lumpy on
    #    purpose: outcome 4 ends up a column of its own at prob 1, outcomes 0-2
    #    are almost entirely borrowed mass, and nothing is left to chance by the
    #    construction -- so the only thing being tested is the draw rule.
    draws = 1_000_000
    trial = random.Random(99)
    counts = Counter(table.sample(trial) for _ in range(draws))
    total = sum(weights)
    print(f"\n{draws} draws        observed  expected   ratio")
    for k, w in enumerate(weights):
        expected = draws * w / total
        print(f"  outcome {k}: p = {w / total:<8.3f}{counts[k]:9d}{expected:10.0f}"
              f"{counts[k] / expected:8.4f}")
    stat = chi_square(counts, weights, draws)
    dof = len(weights) - 1
    print(f"  chi2 = {stat:.2f} on {dof} dof (chi2/dof = {stat / dof:.3f})")
    assert stat < 30.0, stat

    rng = random.Random(20261121)

    # 3. cost per draw against binary search on the CDF
    print("\n      n |  alias probes | cdf probes (mean)")
    for n in (10, 1_000, 100_000):
        w = [rng.random() for _ in range(n)]
        total = sum(w)
        cdf, acc = [], 0.0
        for x in w:
            acc += x / total
            cdf.append(acc)
        cdf[-1] = 1.0
        probes = sum(cdf_probes(cdf, rng.random())[1] for _ in range(2000)) / 2000
        print(f"{n:7d} |             1 | {probes:17.2f}")

    # 4. the same build in floating point leaves a residual behind
    print()
    for n in (100, 10_000, 1_000_000):
        w = [rng.random() ** 4 for _ in range(n)]
        fast = AliasTable(w)
        print(f"n = {n:>7}: float residual {fast.residual:.3e}")
    exact = AliasTable([Fraction(random.Random(7).random()) for _ in range(10_000)],
                       exact=True)
    print(f"n = {10_000:>7}: exact residual {exact.residual:.3e}")
