"""Best rational approximation under a denominator bound.

Given a real x and a bound N, which fraction p/q with 1 <= q <= N sits closest
to x?  The continued-fraction convergents of x are the famous answers -- 22/7,
355/113 -- but they are *sparse*: pi has only five of them below q = 10**6, so
almost every bound N lands in the gap between two convergents, and for such an
N the best fraction is not a convergent at all.  It is a semiconvergent: the
previous convergent plus as many copies of the current one as the bound allows.

Everything is exact.  x is a Fraction, so "closest" compares Fractions and
never floats, and the claim is checked against a brute force over every single
denominator up to N.
"""

from fractions import Fraction
import math
import random


def cf_terms(x):
    """The continued-fraction terms of a Fraction, exactly."""
    n, d = x.numerator, x.denominator
    while d:
        a, r = divmod(n, d)   # floor division, so negatives work too
        yield a
        n, d = d, r


def convergents(x):
    """Yield (p_k, q_k) for each convergent of x, via the usual recurrence."""
    h2, k2 = 0, 1   # p_{-2} / q_{-2}
    h1, k1 = 1, 0   # p_{-1} / q_{-1}
    for a in cf_terms(x):
        h, k = a * h1 + h2, a * k1 + k2
        yield h, k
        h2, k2 = h1, k1
        h1, k1 = h, k


def _closest(x, cands):
    """Closest candidate to x; ties go to the smaller denominator."""
    return min(cands, key=lambda f: (abs(x - f), f.denominator))


def best_rational(x, n):
    """Closest Fraction to x with denominator <= n, in O(log n) steps."""
    if n < 1:
        raise ValueError("denominator bound must be at least 1")
    x = Fraction(x)
    chain = [(1, 0)]          # the virtual predecessor p_{-1}/q_{-1}
    for h, k in convergents(x):
        if k > n:
            break
        chain.append((h, k))
    else:
        return x              # the expansion ended: x itself fits under n

    hp, kp = chain[-2]        # previous convergent
    hc, kc = chain[-1]        # last convergent that fits
    cands = [Fraction(hc, kc)]
    t = (n - kp) // kc        # how many copies of it the bound still allows
    if t > 0:
        cands.append(Fraction(hp + t * hc, kp + t * kc))
    return _closest(x, cands)


def brute(x, n):
    """The same answer by trying every denominator; the reference."""
    x = Fraction(x)
    cands = []
    for q in range(1, n + 1):
        p0 = (x * q).numerator // (x * q).denominator
        cands.append(Fraction(p0, q))
        cands.append(Fraction(p0 + 1, q))
    return _closest(x, cands)


def main():
    rng = random.Random(20261122)

    # 1. Agreement with brute force, on exact rationals.
    for _ in range(2000):
        x = Fraction(rng.randint(-10**6, 10**6), rng.randint(1, 10**6))
        n = rng.randint(1, 70)
        assert best_rational(x, n) == brute(x, n), (x, n)
    print("brute force: 2000 random (x, N) pairs, exact agreement")

    # 2. Agreement with the standard library.
    ties = 0
    for _ in range(2000):
        x = Fraction(rng.randint(1, 10**9), rng.randint(1, 10**9))
        n = rng.randint(1, 10**4)
        mine, theirs = best_rational(x, n), x.limit_denominator(n)
        if mine != theirs:
            assert abs(x - mine) == abs(x - theirs), (x, n, mine, theirs)
            ties += 1
    print(f"Fraction.limit_denominator: 2000 pairs agree, {ties} exact ties")

    # 3. How often is the answer NOT a convergent?
    semis = total = 0
    for _ in range(3000):
        x = Fraction(rng.randint(1, 10**9), rng.randint(1, 10**9))
        n = rng.randint(2, 10**5)
        best = best_rational(x, n)
        seen = {Fraction(h, k) for h, k in convergents(x) if k <= n}
        total += 1
        semis += best not in seen
    print(f"not a convergent: {semis}/{total} = {100*semis/total:.1f}% of cases")

    # 4. pi, which is exactly a Fraction once it is a float.
    pi = Fraction(math.pi)
    print("\n  N        best p/q     error        convergent?")
    for n in (7, 10, 56, 99, 100, 112, 113, 10**4):
        f = best_rational(pi, n)
        is_c = any(k == f.denominator and h == f.numerator
                   for h, k in convergents(pi))
        err = float(abs(pi - f))
        print(f"{n:>6}  {str(f):>12}  {err:.3e}   {'yes' if is_c else 'no'}")

    # The gap in detail: 22/7 is the best convergent for every N from 7 to 105,
    # yet it is the best *fraction* only up to N = 56.
    best_conv = Fraction(22, 7)
    beaten = [n for n in range(7, 114) if best_rational(pi, n) != best_conv
              and best_rational(pi, n).denominator <= 105]
    print(f"\n22/7 is the best convergent for N = 7..105, but is beaten "
          f"from N = {beaten[0]} onward, first by {best_rational(pi, beaten[0])}")
    print("all checks passed")


if __name__ == "__main__":
    main()
