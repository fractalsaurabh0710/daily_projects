"""Welzl's smallest enclosing circle: expected O(n), three nested loops deep.

The surprise is that three nested loops run in linear expected time. The reason
is backwards analysis: the smallest circle of a set is pinned by at most 3 of its
points, so after a random shuffle the probability that point i falls outside the
circle of the first i-1 is at most 3/i. The i-th restart costs O(i), and
sum_i (3/i) * O(i) = O(n). The loops are nested; the work is not.

Run directly to check against brute force and measure that 3/i prediction.
"""

import itertools
import math
import random

STATS = {"restarts": 0, "two_pt": 0, "three_pt": 0}


def _dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])


def _in_circle(c, p, eps=1e-9):
    return _dist(c[0], p) <= c[1] + eps


def _from_two(a, b):
    """Circle with a and b as a diameter -- the smallest holding just those two."""
    centre = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    return (centre, _dist(a, b) / 2)


def _from_three(a, b, c):
    """Circumcircle, or None if the three points are collinear."""
    ax, ay = a
    bx, by = b
    cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    if abs(d) < 1e-14:
        return None
    a2, b2, c2 = ax * ax + ay * ay, bx * bx + by * by, cx * cx + cy * cy
    ux = (a2 * (by - cy) + b2 * (cy - ay) + c2 * (ay - by)) / d
    uy = (a2 * (cx - bx) + b2 * (ax - cx) + c2 * (bx - ax)) / d
    centre = (ux, uy)
    return (centre, max(_dist(centre, p) for p in (a, b, c)))


def smallest_enclosing_circle(points, rng=random):
    """Smallest circle containing every point, as ((x, y), radius)."""
    pts = list(dict.fromkeys(map(tuple, points)))  # duplicates change nothing
    if not pts:
        return None
    rng.shuffle(pts)

    circle = (pts[0], 0.0)
    for i in range(1, len(pts)):
        if _in_circle(circle, pts[i]):
            continue
        # pts[i] is outside, so it must lie ON the boundary of the answer for
        # pts[:i+1]. Rebuild from scratch with it pinned there.
        STATS["restarts"] += 1
        circle = (pts[i], 0.0)
        for j in range(i):
            if _in_circle(circle, pts[j]):
                continue
            STATS["two_pt"] += 1
            circle = _from_two(pts[i], pts[j])
            for k in range(j):
                if _in_circle(circle, pts[k]):
                    continue
                STATS["three_pt"] += 1
                cand = _from_three(pts[i], pts[j], pts[k])
                if cand is not None:
                    circle = cand
    return circle


def brute_force(points):
    """Every pair and triple, keep the smallest circle that holds everything."""
    pts = list(dict.fromkeys(map(tuple, points)))
    if not pts:
        return None
    if len(pts) == 1:
        return (pts[0], 0.0)
    best = None
    cands = [_from_two(a, b) for a, b in itertools.combinations(pts, 2)]
    cands += [c for c in (_from_three(*t) for t in itertools.combinations(pts, 3)) if c]
    for c in cands:
        if all(_in_circle(c, p) for p in pts) and (best is None or c[1] < best[1]):
            best = c
    return best


def _check_minimal(circle, pts):
    """Every point inside, and 2 or 3 of them exactly on the boundary."""
    assert all(_in_circle(circle, p) for p in pts), "point escaped the circle"
    on = sum(1 for p in pts if abs(_dist(circle[0], p) - circle[1]) < 1e-7)
    assert on >= 2 or len(set(map(tuple, pts))) == 1, f"only {on} support points"


if __name__ == "__main__":
    rng = random.Random(7)

    # Agreement with brute force, including collinear and duplicate-heavy sets.
    for trial in range(400):
        n = rng.randint(1, 9)
        pts = [(rng.randint(-20, 20), rng.randint(-20, 20)) for _ in range(n)]
        if trial % 5 == 0:  # collinear
            pts = [(t, 2 * t + 1) for t in rng.sample(range(-20, 21), n)]
        if trial % 7 == 0:  # duplicates
            pts = [pts[0]] * (n - 1) + pts[-1:]
        got, want = smallest_enclosing_circle(pts, rng), brute_force(pts)
        assert abs(got[1] - want[1]) < 1e-7, (pts, got, want)
        _check_minimal(got, pts)
    print("400 random sets (incl. collinear, duplicates) match brute force")

    # A circle's own boundary points: the answer is that circle.
    ring = [(5 + 3 * math.cos(t), -2 + 3 * math.sin(t)) for t in
            [i * 2 * math.pi / 60 for i in range(60)]]
    c = smallest_enclosing_circle(ring, rng)
    assert abs(c[1] - 3) < 1e-9 and _dist(c[0], (5, -2)) < 1e-9, c
    print(f"60 points on a known circle    -> centre {c[0][0]:.6f},{c[0][1]:.6f} r {c[1]:.9f}")

    # The 3/i prediction: expected restarts over n points is ~sum 3/i ~ 3 ln n.
    print()
    print("  n     restarts   3*ln(n)   two_pt   three_pt")
    for n in (100, 1_000, 10_000, 50_000):
        STATS.update(restarts=0, two_pt=0, three_pt=0)
        trials = max(1, 20_000 // n)
        for _ in range(trials):
            pts = [(rng.random(), rng.random()) for _ in range(n)]
            smallest_enclosing_circle(pts, rng)
        r, t2, t3 = (STATS[k] / trials for k in ("restarts", "two_pt", "three_pt"))
        print(f"{n:>6}  {r:9.1f}  {3*math.log(n):8.1f}  {t2:7.1f}  {t3:9.1f}")
    print()
    print("Restarts track 3*ln(n), not n -- which is why nesting three loops")
    print("still costs O(n): the deep ones almost never fire.")
