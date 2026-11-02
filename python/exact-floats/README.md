# Exact Floats

Prints the exact decimal value of a float — all of it. `0.1` is really
`0.1000000000000000055511151231257827021181583404541015625`, and this prints
that, plus the shortest decimal that still means the same float, plus the
float's immediate neighbours and the gap between them.

## Run

    python3 exact_floats.py

Runs its tests, then a short tour: the `0.1 + 0.2` carry made visible, how long
various expansions are, and where `float` stops being able to count integers.

## The interesting part

There is no rounding in `exact_decimal()`. A float is `n / 2**k`, and
multiplying top and bottom by `5**k` makes the denominator `10**k` — a decimal
point, nothing more. So every binary float terminates in base 10; the question
is only how long it takes. `0.1` needs 55 digits, `1e-10` needs 77, and the
smallest subnormal `5e-324` needs 751 — a number whose shortest honest name is
one digit long and whose exact name is three quarters of a kilobyte.

`next_up()` leans on a different piece of IEEE 754: positive floats are laid
out so that incrementing the raw 64-bit integer lands on the next
representable value, exponent carries included. Hence `ulp(2**53) == 2.0`, and
`2.0**53 + 1 == 2.0**53`.

Standard library only (`struct` for the bit walk).
