"""Compensated summation: what Kahan's trick recovers, and what it drops.

Four float summation strategies plus `math.fsum`, each measured against the
exact answer. The point of interest is that Kahan summation -- the textbook
fix for accumulated rounding error -- silently loses a term whenever the
next addend is larger than the running total, while Neumaier's one extra
branch recovers it.

Run: python3 sums.py
"""

import decimal
import math
import random
from fractions import Fraction

EPS = 2.0 ** -53


def naive(xs):
    s = 0.0
    for x in xs:
        s += x
    return s


def kahan(xs, trace=None):
    s = c = 0.0
    for x in xs:
        y = x - c          # y assumes the lost bits live in the addend
        t = s + y
        c = (t - s) - y    # ...so this measures nothing when |x| > |s|
        s = t
        if trace is not None:
            trace.append((x, s, c))
    return s


def neumaier(xs, trace=None):
    s = c = 0.0
    for x in xs:
        t = s + x
        if abs(s) >= abs(x):
            c += (s - t) + x   # small addend: the bits fall off x
        else:
            c += (x - t) + s   # large addend: the bits fall off s
        s = t
        if trace is not None:
            trace.append((x, s, c))
    return s + c


def pairwise(xs, cutoff=16):
    if len(xs) <= cutoff:
        return naive(xs)
    mid = len(xs) // 2
    return pairwise(xs[:mid], cutoff) + pairwise(xs[mid:], cutoff)


def exact(xs):
    """The true sum, rounded once at the end."""
    return Fraction(sum(Fraction(x) for x in xs))


def rel_err(got, want):
    want = Fraction(want)
    if want == 0:
        return 0.0 if got == 0.0 else math.inf
    return abs(float((Fraction(got) - want) / want))


METHODS = [("naive", naive), ("kahan", kahan), ("neumaier", neumaier),
           ("pairwise", pairwise), ("fsum", math.fsum)]


def classic_case():
    xs = [1.0, 1e100, 1.0, -1e100]
    print("1. [1, 1e100, 1, -1e100], exact sum = 2")
    for name, fn in METHODS:
        print(f"   {name:9} {fn(xs)!r}")
    kt, nt = [], []
    kahan(xs, kt)
    neumaier(xs, nt)
    print("   step  addend      kahan c   neumaier c")
    for (x, _, kc), (_, _, nc) in zip(kt, nt):
        print(f"   {x:>11.0e}   {kc:>10.1f}   {nc:>10.1f}")
    print("   kahan's c is 0 after the 1e100: it asked x what it lost,")
    print("   but the dropped bit was in s. neumaier's branch asks s.\n")
    assert kahan(xs) == 0.0 and neumaier(xs) == 2.0 and math.fsum(xs) == 2.0


def ill_conditioned(n, scale, target, rng):
    """Sum is exactly `target`: every other term is cancelled by its negation."""
    half = [rng.uniform(1.0, 2.0) * scale for _ in range(n // 2)]
    xs = half + [-v for v in half] + [target]
    rng.shuffle(xs)
    return xs


def conditioning_sweep():
    rng = random.Random(7)
    print("2. 1001 terms summing to exactly 1.0, cancellation increasing")
    print("   cond        naive      kahan   neumaier   pairwise   fsum")
    worst = {name: 0.0 for name, _ in METHODS}
    for scale in (1e0, 1e4, 1e8, 1e12, 1e16):
        xs = ill_conditioned(1000, scale, 1.0, rng)
        assert exact(xs) == 1
        cond = sum(abs(x) for x in xs)
        row = f"   {cond:8.1e}"
        for name, fn in METHODS:
            e = rel_err(fn(xs), 1)
            worst[name] = max(worst[name], e)
            row += f"  {e:9.1e}"
        print(row)
    print("   naive error tracks cond * n * eps. neumaier is exact on every row")
    print("   here only because this data cancels in exact pairs -- but note that")
    print("   at the last row pairwise beats kahan, which has run out of road.\n")
    assert worst["fsum"] == 0.0
    assert worst["neumaier"] <= worst["kahan"] <= worst["naive"]


def drift():
    n = 1_000_000
    xs = [0.1] * n
    truth = Fraction(0.1) * n
    nearest = float(truth)
    ulp = math.ulp(nearest)
    with decimal.localcontext() as ctx:
        ctx.prec = 40
        as_dec = decimal.Decimal(0.1) * n
    print(f"3. 0.1 added {n:,} times")
    print(f"   exact real sum   {as_dec}")
    print(f"   nearest double   {nearest!r}   (1 ulp = {ulp:.3e})")
    for name, fn in METHODS:
        got = fn(xs)
        off = float(Fraction(got) - truth)
        print(f"   {name:9}  {got:<20.17g} {off:+.3e}  = {off / ulp:>+10.1f} ulp")
    print("   the exact sum is not representable, so being 0.4 ulp low *is* the")
    print("   right answer; naive is 91000 ulps high because by the end its total")
    print("   is 1e6 times larger than the term being added to it.\n")
    assert Fraction(math.fsum(xs)) == Fraction(nearest)


if __name__ == "__main__":
    classic_case()
    conditioning_sweep()
    drift()
    print("all assertions passed")
