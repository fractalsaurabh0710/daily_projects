# Best Rationals

The closest fraction `p/q` to a real `x` with `q <= N`, found in O(log N) steps
instead of N, and proved correct against a brute force over every denominator.

## Run

    python3 main.py

No dependencies. It runs its own checks and prints the table.

## The interesting part

The continued-fraction convergents of a number are the textbook "best
approximations" -- `22/7`, `355/113` for pi -- but there are only a handful of
them, so most bounds `N` fall in the gap between two. In that gap the best
fraction is a **semiconvergent**: the previous convergent plus `t` copies of the
current one, with `t` as large as the bound allows.

For pi, `22/7` is the largest convergent with denominator under 106, yet it stops
being the best fraction at `N = 57`, where `179/57` overtakes it, and by `N = 99`
the answer is `311/99` -- seven times more accurate than `22/7` and not a
convergent at all. Across 3000 random `(x, N)` pairs the answer is a
non-convergent 22.3% of the time.

Everything is `Fraction` arithmetic, so "closest" is an exact comparison rather
than a float one, which is what makes the brute-force check meaningful: 2000
random pairs agree exactly, and 2000 more agree with
`Fraction.limit_denominator`, whose algorithm this is.
