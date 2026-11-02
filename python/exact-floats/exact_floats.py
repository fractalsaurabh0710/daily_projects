"""Every float is exactly a finite decimal. Here are those decimals.

A binary float is a ratio n / 2**k, and 1/2 = 0.5 exactly, so every float
terminates in base 10 -- there is no rounding anywhere in exact_decimal(),
just n * 5**k with the point moved k places. The surprising part is how long
those decimals are: 0.1 is 55 digits, and 1e308 is a 309-digit integer.

Run directly to see the tests and a short tour:  python3 exact_floats.py
"""

import struct

__all__ = ["exact_decimal", "shortest_roundtrip", "next_up", "next_down", "ulp"]


# --------------------------------------------------------------------------
# The exact value
# --------------------------------------------------------------------------

def exact_decimal(x):
    """The exact decimal expansion of a float, with no digits invented or lost.

    as_integer_ratio() gives n / 2**k.  Multiplying top and bottom by 5**k
    turns the denominator into 10**k, which is just a decimal point.
    """
    x = float(x)
    if x != x or x in (float("inf"), float("-inf")):
        return repr(x)

    n, d = x.as_integer_ratio()
    sign = "-" if n < 0 else ""
    n = abs(n)
    k = d.bit_length() - 1            # d is always a power of two
    digits = str(n * 5 ** k)

    if k == 0:
        return sign + digits
    digits = digits.rjust(k + 1, "0")
    return sign + digits[:-k] + "." + digits[-k:]


def significant_digits(x):
    """How many digits the exact expansion of x actually needs."""
    body = exact_decimal(x).lstrip("-").replace(".", "").lstrip("0")
    return len(body.rstrip("0")) if body else 0


# --------------------------------------------------------------------------
# The shortest decimal that means the same float
# --------------------------------------------------------------------------

def shortest_roundtrip(x):
    """Fewest significant digits whose nearest float is still exactly x.

    This is what repr() prints.  Found here by asking, rather than by the
    Grisu/Ryu arithmetic that makes it fast: format to p digits, parse back,
    stop when the trip is lossless.  17 always suffices for float64.
    """
    x = float(x)
    for p in range(1, 18):
        s = "%.*e" % (p - 1, x)
        if float(s) == x:
            return s
    raise AssertionError("17 digits should always round-trip")


# --------------------------------------------------------------------------
# The neighbours
# --------------------------------------------------------------------------

def _bits(x):
    return struct.unpack("<Q", struct.pack("<d", x))[0]


def _unbits(b):
    return struct.unpack("<d", struct.pack("<Q", b))[0]


def next_up(x):
    """The smallest float greater than x, by walking the bit pattern.

    IEEE 754 lays out positive floats so that incrementing the 64-bit
    integer lands on the next representable value -- exponent carries into
    place on its own.  Negative zero has to hop across to positive.
    """
    x = float(x)
    if x != x or x == float("inf"):
        return x
    if x == 0.0:
        return _unbits(1)                       # covers -0.0 too
    b = _bits(x)
    return _unbits(b + 1) if x > 0 else _unbits(b - 1)


def next_down(x):
    return -next_up(-float(x))


def ulp(x):
    """The gap to the next float: the real resolution at this magnitude."""
    return next_up(abs(float(x))) - abs(float(x))


# --------------------------------------------------------------------------
# Tests
# --------------------------------------------------------------------------

def _test():
    # Exactly representable values print clean.
    assert exact_decimal(0.5) == "0.5"
    assert exact_decimal(0.25) == "0.25"
    assert exact_decimal(-2.0) == "-2"
    assert exact_decimal(0.0) == "0"

    # 0.1 is not 0.1, and this is what it is instead.
    assert exact_decimal(0.1) == (
        "0.1000000000000000055511151231257827021181583404541015625")
    assert significant_digits(0.1) == 55

    # The classic, with the carry made visible.
    assert exact_decimal(0.1 + 0.2) == (
        "0.3000000000000000444089209850062616169452667236328125")
    assert exact_decimal(0.3) == (
        "0.299999999999999988897769753748434595763683319091796875")
    assert 0.1 + 0.2 != 0.3

    # Exact means exact: parse the expansion back and get the float again.
    for v in (0.1, 0.2, 1 / 3, 1e-300, 1e300, 123.456, 2 ** 70 + 1.0):
        assert float(exact_decimal(v)) == v

    # Shortest round-trip agrees with repr, digit for digit.
    for v in (0.1, 0.3, 1 / 3, 5e-324, 1e22, 0.30000000000000004):
        assert float(shortest_roundtrip(v)) == v
        count = lambda s: len(s.split("e")[0].replace(".", "").replace("-", "")
                              .lstrip("0").rstrip("0")) or 1
        assert count(shortest_roundtrip(v)) == count(repr(v)), v

    # Neighbours and the gap between them.
    assert next_up(0.0) == 5e-324                  # smallest subnormal
    assert next_down(0.0) == -5e-324
    assert next_up(-0.0) == 5e-324
    assert next_up(1.0) == 1 + 2 ** -52
    assert next_down(next_up(1.0)) == 1.0
    assert ulp(1.0) == 2 ** -52
    assert ulp(2 ** 52) == 1.0                     # integers stop being exact
    assert ulp(2 ** 53) == 2.0                     # ...here: 2**53+1 is unrepresentable
    assert 2.0 ** 53 + 1 == 2.0 ** 53
    print("all tests passed")


def _tour():
    print("\nexact values")
    for v in (0.1, 0.2, 0.3, 0.1 + 0.2):
        print("  %-22s %s" % (repr(v), exact_decimal(v)))

    print("\nhow long the exact expansion is")
    for v in (0.5, 0.1, 1 / 3, 1e-10, 5e-324):
        print("  %-10s %4d significant digits" % (repr(v), significant_digits(v)))

    print("\nresolution at different magnitudes")
    for v in (1.0, 1e6, 2.0 ** 52, 2.0 ** 53, 1e300):
        print("  near %-10s next float is %s away" % ("%g" % v, "%g" % ulp(v)))

    print("\nneighbours of 1.0")
    for v in (next_down(1.0), 1.0, next_up(1.0)):
        print("  %s" % exact_decimal(v))


if __name__ == "__main__":
    _test()
    _tour()
