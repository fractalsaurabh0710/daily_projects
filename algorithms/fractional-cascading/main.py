"""Fractional cascading: one binary search, then O(1) per list.

Given k sorted lists and a query q, finding q's successor in every list costs
k * log n if you binary search each one. Fractional cascading gets it down to
log n + O(k) by merging every *second* element of each list into the one above
it and remembering where it came from -- a "bridge". The first binary search
lands you in the top list; after that each level is a pointer hop plus at most
two steps of scanning, because the promoted elements are dense enough that no
two consecutive positions can both be missed.

Run: python3 main.py
"""

import bisect
import random

# --- build ------------------------------------------------------------------
# M[i] holds entries (value, own, src):
#   own = index into lists[i] if this is a real element of lists[i], else -1
#   src = position in M[i+1] this entry was promoted from, else -1


def build(lists):
    k = len(lists)
    M = [None] * k
    for i in range(k - 1, -1, -1):
        base = [(v, j, -1) for j, v in enumerate(lists[i])]
        if i == k - 1:
            M[i] = base
        else:
            promoted = [(M[i + 1][p][0], -1, p) for p in range(0, len(M[i + 1]), 2)]
            M[i] = sorted(base + promoted, key=lambda e: (e[0], 0 if e[1] >= 0 else 1))

    own_fwd, bridge = [], []
    for i in range(k):
        m, n = M[i], len(M[i])

        # first real element of lists[i] at position >= j
        of = [-1] * (n + 1)
        for j in range(n - 1, -1, -1):
            of[j] = m[j][1] if m[j][1] >= 0 else of[j + 1]
        own_fwd.append(of)

        # source position of the last promoted entry at position STRICTLY < j.
        # Strictly: an entry at position j itself may already be >= q, and its
        # source would then sit at or past the answer in M[i+1], so the scan
        # below would start too late and miss it.
        br, last = [0] * (n + 1), 0
        for j in range(n + 1):
            br[j] = last
            if j < n and m[j][2] >= 0:
                last = m[j][2]
        bridge.append(br)

    return M, own_fwd, bridge


# --- query ------------------------------------------------------------------


def successors(struct, q, stats):
    M, own_fwd, bridge = struct
    lo, hi = 0, len(M[0])
    while lo < hi:
        mid = (lo + hi) // 2
        stats["cmp"] += 1
        if M[0][mid][0] < q:
            lo = mid + 1
        else:
            hi = mid
    p, out = lo, []
    for i in range(len(M)):
        out.append(own_fwd[i][p])
        if i + 1 == len(M):
            break
        m, p, steps = M[i + 1], bridge[i][p], 0
        while p < len(m):
            stats["cmp"] += 1
            if m[p][0] < q:
                p, steps = p + 1, steps + 1
            else:
                break
        stats["max_steps"] = max(stats["max_steps"], steps)
    return out


def successors_naive(lists, q, stats):
    out = []
    for L in lists:
        lo, hi = 0, len(L)
        while lo < hi:
            mid = (lo + hi) // 2
            stats["cmp"] += 1
            if L[mid] < q:
                lo = mid + 1
            else:
                hi = mid
        out.append(lo if lo < len(L) else -1)
    return out


# --- demo -------------------------------------------------------------------


def fresh():
    return {"cmp": 0, "max_steps": 0}


def make_lists(k, n, rng, hi=10**6):
    return [sorted(rng.sample(range(hi), n)) for _ in range(k)]


def main():
    rng = random.Random(7)

    # correctness: the structure must agree with bisect on every list
    for trial in range(40):
        k, n = rng.randint(1, 12), rng.randint(0, 40)
        lists = make_lists(k, n, rng, hi=120)
        struct = build(lists)
        for q in range(-2, 124):
            got = successors(struct, q, fresh())
            want = [
                (bisect.bisect_left(L, q) if bisect.bisect_left(L, q) < len(L) else -1)
                for L in lists
            ]
            assert got == want, (trial, q, got, want)
    print("correctness: 40 random structures x 126 queries agree with bisect")

    # the augmented lists cost at most 2x the input, by geometric series
    lists = make_lists(40, 2000, rng)
    struct = build(lists)
    total_in = sum(len(L) for L in lists)
    total_aug = sum(len(m) for m in struct[0])
    print(f"space: {total_in} elements -> {total_aug} augmented ({total_aug/total_in:.3f}x)")
    del lists, struct

    # comparison counts, averaged over queries
    queries = [rng.randrange(10**6) for _ in range(200)]
    print("\n  k      n   naive cmp/query   cascaded   speedup   max scan steps")
    for k, n in ((16, 256), (16, 16384), (64, 256), (64, 4096)):
        lists = make_lists(k, n, rng)
        struct = build(lists)
        a, b = fresh(), fresh()
        for q in queries:
            assert successors(struct, q, b) == successors_naive(lists, q, a)
        na, ca = a["cmp"] / len(queries), b["cmp"] / len(queries)
        print(f"{k:>4}{n:>7}{na:>16.1f}{ca:>12.1f}{na/ca:>10.2f}x{b['max_steps']:>16}")
        del lists, struct

    print("\nNaive grows as k*log2(n); cascaded as log2(2n) + ~2k, so the win widens")
    print("with n and narrows with k -- and no scan ever took more than 2 steps.")


if __name__ == "__main__":
    main()
