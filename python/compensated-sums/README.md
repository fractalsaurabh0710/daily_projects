# Compensated Sums

Five ways to add up a list of floats -- naive, Kahan, Neumaier, pairwise, and
`math.fsum` -- each scored against the exact answer computed with
`fractions.Fraction`, so the error figures are measured rather than estimated.

```
python3 sums.py
```

The interesting part is that Kahan summation, the standard fix for accumulated
rounding error, drops a term outright when the next addend is larger than the
running total. Its correction is `c = (t - s) - y`, which asks the *addend*
what the addition rounded away -- but in that case the discarded bits were in
`s`, so `c` comes back 0 and the information is gone. Neumaier's version
branches on `abs(s) >= abs(x)` and asks whichever operand actually lost the
bits, which costs one comparison and recovers the term. `[1, 1e100, 1, -1e100]`
sums to `0.0` under Kahan and `2.0` under Neumaier.

Pairwise summation is doing something different from both: it reduces the
*depth* of the addition chain, not the error of each step, so it does nothing
for the `1e100` case and yet beats Kahan on the most ill-conditioned row of
the sweep.

Script output is deterministic -- the random data is seeded, and the test data
is built so its exact sum is known in closed form (every term is cancelled by
its own negation, plus one leftover).
