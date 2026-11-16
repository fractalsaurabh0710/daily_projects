"""CPython's cycle detector, reimplemented in pure Python.

Reference counting frees an object the moment its count hits zero, which is
why it cannot free a cycle: every node in a cycle is kept alive by another
node in the same cycle, so no count ever reaches zero.  CPython's garbage
collector settles this with one trick, implemented here.

Given a set of candidate containers (a "generation"), copy each object's real
reference count, then walk the candidates and subtract one for every reference
that comes *from inside the set*.  What is left over for an object is the
number of references reaching it from outside.  An object with a leftover
above zero is externally reachable, hence a root; anything reachable from a
root survives; everything else is garbage -- regardless of how high its raw
reference count was.

Nodes here are plain lists, so each graph node is exactly one GC-tracked
object with no hidden instance dict to confuse the bookkeeping.

Run:  python3 gc_cycles.py
"""

import gc
import random
import sys


def _probe_overhead():
    """References an object in the candidate list owes to this module's own
    bookkeeping: the list slot, the loop variable, and getrefcount's argument.
    Measured rather than assumed, with a probe built the same way."""
    probe = [[]]
    return min(sys.getrefcount(o) for o in probe)


_OVERHEAD = _probe_overhead()


def predict_unreachable(objs):
    """Return (unreachable_ids, external_refs) for the candidate set `objs`.

    `objs` must hold each candidate exactly once and must be the only
    container of the set, mirroring a real GC generation.
    """
    inside = {id(o) for o in objs}
    if len(inside) != len(objs):
        raise ValueError("candidates must be distinct objects")

    # Step 1: copy the real reference counts, minus what we ourselves hold.
    gc_refs = {id(o): sys.getrefcount(o) - _OVERHEAD for o in objs}

    # Step 2: subtract every reference originating inside the candidate set.
    for o in objs:
        for r in gc.get_referents(o):
            if id(r) in inside:
                gc_refs[id(r)] -= 1

    # Step 3: whatever is left over came from outside -- those are the roots.
    stack = [o for o in objs if gc_refs[id(o)] > 0]
    reachable = {id(o) for o in stack}
    while stack:
        for r in gc.get_referents(stack.pop()):
            if id(r) in inside and id(r) not in reachable:
                reachable.add(id(r))
                stack.append(r)

    return inside - reachable, gc_refs


def cyclic_core(objs, unreachable):
    """The part of `unreachable` that reference counting alone cannot free.

    Garbage with no incoming reference dies the instant the generation list
    drops it, and its death cascades.  Peel those away repeatedly; what
    survives is cyclic, and is exactly what gc.collect() ends up reporting.
    """
    remaining = set(unreachable)
    byid = {id(o): o for o in objs if id(o) in remaining}
    while True:
        indeg = dict.fromkeys(remaining, 0)
        for i in remaining:
            for r in gc.get_referents(byid[i]):
                if id(r) in remaining:
                    indeg[id(r)] += 1
        dead = {i for i, d in indeg.items() if d == 0}
        if not dead:
            return remaining
        remaining -= dead


def reachable_from(roots, inside):
    """Plain graph reachability -- the ground truth the refcount trick must match."""
    stack = list(roots)
    seen = {id(o) for o in stack}
    while stack:
        for r in gc.get_referents(stack.pop()):
            if id(r) in inside and id(r) not in seen:
                seen.add(id(r))
                stack.append(r)
    return seen


def build_graph(rng, n=24, out_degree=2, n_live=3):
    """A random digraph of list-nodes, plus the handful held by a live root."""
    nodes = [[] for _ in range(n)]
    for node in nodes:
        for j in rng.sample(range(n), out_degree):
            node.append(nodes[j])
    live = [nodes[i] for i in rng.sample(range(n), n_live)]
    return nodes, live


def test_against_reachability(trials=400):
    rng = random.Random(7)
    cyclic_total = 0
    for _ in range(trials):
        objs, live = build_graph(rng)
        unreachable, _ = predict_unreachable(objs)
        inside = {id(o) for o in objs}
        expected = inside - reachable_from(live, inside)
        assert unreachable == expected, "refcount verdict disagreed with reachability"
        cyclic_total += len(cyclic_core(objs, unreachable))
    print(f"ok  {trials} random graphs: refcount leftovers matched reachability exactly")
    print(f"    {cyclic_total} unreachable nodes across them needed the cycle collector")


def test_against_real_gc(trials=20):
    rng = random.Random(11)
    gc.disable()
    try:
        for _ in range(trials):
            objs, live = build_graph(rng, n=30)
            unreachable, _ = predict_unreachable(objs)
            predicted = len(cyclic_core(objs, unreachable))
            gc.collect()          # clear our own scratch garbage; objs still holds the graph
            del objs
            assert gc.collect() == predicted, "CPython collected a different number"
            del live
    finally:
        gc.enable()
    print(f"ok  {trials} graphs: predicted cyclic garbage matched gc.collect() exactly")


def _closed_cycle():
    """Built in its own frame: once it returns, the only references left to
    these three lists are the cycle itself and the returned list."""
    a, b, c = [], [], []
    a.append(b)
    b.append(c)
    c.append(a)
    return [a, b, c]


def test_pure_cycle():
    objs = _closed_cycle()
    counts = [sys.getrefcount(o) - _OVERHEAD for o in objs]
    unreachable, gc_refs = predict_unreachable(objs)
    assert len(unreachable) == 3, "a closed cycle with no external owner is garbage"
    assert all(v == 0 for v in gc_refs.values())
    print(f"ok  closed 3-cycle: raw refcounts {counts}, external refs "
          f"{sorted(gc_refs.values())} -> all 3 unreachable")


if __name__ == "__main__":
    print(f"bookkeeping overhead measured at {_OVERHEAD} references per candidate\n")
    test_pure_cycle()
    test_against_reachability()
    test_against_real_gc()
