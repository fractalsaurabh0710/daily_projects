# Smallest Enclosing Circle

Welzl's algorithm: the smallest circle containing a set of points, found by three
nested loops that together run in expected linear time.

## Run

    python3 circle.py

Checks itself against brute force on 400 random point sets — collinear and
duplicate-heavy ones included — then prints how often each loop level actually
fires as `n` grows.

## The interesting part

Three nested loops that look like `O(n^3)` are `O(n)` expected, and the reason is
*backwards* analysis rather than anything about the loops.

The smallest enclosing circle of any set is pinned by at most 3 of its points. So
if the points are shuffled first, the chance that point `i` lies outside the
circle of the first `i-1` is at most `3/i` — it would have to be one of the three
that define the answer for that prefix. When it does fall outside, it must lie on
the boundary of the new answer, so the inner loop rebuilds from scratch with that
point pinned, at cost `O(i)`. Summed:

    sum over i of (3/i) * O(i) = O(n)

The measurement is the claim, not the asymptotic:

      n     restarts   3*ln(n)
    100       10.4      13.8
    1000      14.6      20.7
    10000     16.0      27.6
    50000     24.0      32.5

Restarts grow logarithmically while `n` grows 500x. The second and third loops
fire a few hundred times total across 50,000 points. (Large-`n` rows average
fewer trials, so they are noisier — the shape is the point.)

One more thing worth noting: `_from_three` returns `None` for collinear points
rather than dividing by a zero determinant, and the caller keeps its previous
circle. That is correct, not a patch — three collinear points have no
circumcircle, and the two-point circle already covering them is the right answer.
