"""C3 linearization from scratch, checked against the MRO CPython actually builds.

`type.__mro__` is computed by the C3 algorithm, and C3 is short enough to write
out by hand -- so this builds random class hierarchies, linearizes them here,
and asserts the result equals CPython's, name for name, including the cases
where no linearization exists and both implementations must refuse.
"""

import random


class Inconsistent(Exception):
    """No linearization exists for these bases."""


def merge(sequences):
    """C3 merge: repeatedly take a head that appears in no sequence's tail."""
    sequences = [list(s) for s in sequences]
    out = []
    while True:
        sequences = [s for s in sequences if s]
        if not sequences:
            return out
        for seq in sequences:
            head = seq[0]
            # A head that appears in some tail must wait: something still
            # has to precede it. If every candidate is blocked, the order
            # the bases ask for is self-contradictory.
            if not any(head in other[1:] for other in sequences):
                break
        else:
            raise Inconsistent(
                "no head left: " + ", ".join(repr(s) for s in sequences)
            )
        out.append(head)
        for seq in sequences:
            if seq and seq[0] == head:
                del seq[0]


def linearize(name, bases, mros):
    """MRO of `name`: itself, then the merge of its bases' MROs and its bases.

    The bases list is merged in as a sequence of its own -- that is what makes
    local precedence order binding, so `class Z(X, Y)` can never put Y first.
    """
    return [name] + merge([mros[b] for b in bases] + [list(bases)])


def model(spec):
    """Linearize a whole hierarchy here. spec: [(name, (base, ...)), ...]."""
    mros = {"object": ["object"]}
    for name, bases in spec:
        mros[name] = linearize(name, bases or ("object",), mros)
    return mros


def realize(spec):
    """Build the same hierarchy as real classes and read off CPython's MROs."""
    classes = {"object": object}
    mros = {"object": ["object"]}
    for name, bases in spec:
        cls = type(name, tuple(classes[b] for b in bases), {})
        classes[name] = cls
        mros[name] = [c.__name__ for c in cls.__mro__]
    return mros


def compare(spec):
    """Return ('ok', n) if both agree, or ('rejected',) if both refuse."""
    try:
        mine = model(spec)
    except Inconsistent:
        mine = None
    try:
        theirs = realize(spec)
    except TypeError:
        theirs = None
    if (mine is None) != (theirs is None):
        raise AssertionError(f"disagreement on {spec}: {mine} vs {theirs}")
    if mine is None:
        return ("rejected",)
    for name, _ in spec:
        assert mine[name] == theirs[name], (name, mine[name], theirs[name])
    return ("ok", len(spec))


def random_spec(rng, n):
    """A hierarchy of n classes, each inheriting from 1-3 earlier ones."""
    names = [chr(ord("A") + i) for i in range(n)]
    spec = []
    for i, name in enumerate(names):
        pool = names[:i] or ["object"]
        k = min(rng.randint(1, 3), len(pool))
        spec.append((name, tuple(rng.sample(pool, k))))
    return spec


DIAMOND = [("A", ()), ("B", ()), ("X", ("A", "B")), ("Y", ("B", "A"))]


def main():
    # The textbook pair: X wants A before B, Y wants B before A, so a class
    # inheriting from both cannot order them. Each on its own is fine.
    assert compare(DIAMOND) == ("ok", 4)
    assert compare(DIAMOND + [("Z", ("X", "Y"))]) == ("rejected",)

    # A deeper diamond, where the merge has to reach past a shared ancestor.
    spec = [("A", ()), ("B", ("A",)), ("C", ("A",)), ("D", ("B", "C"))]
    assert model(spec)["D"] == ["D", "B", "C", "A", "object"]

    rng = random.Random(20261110)
    ok = rejected = 0
    widest = []
    for _ in range(4000):
        spec = random_spec(rng, rng.randint(2, 9))
        result = compare(spec)
        if result[0] == "ok":
            ok += 1
            last = model(spec)[spec[-1][0]]
            widest = max(widest, last, key=len)
        else:
            rejected += 1

    print(f"{ok + rejected} random hierarchies: {ok} linearized, "
          f"{rejected} unlinearizable -- CPython agreed on every one")
    print(f"longest MRO found: {' -> '.join(widest)}")
    print("C3 refused exactly when CPython raised TypeError")


if __name__ == "__main__":
    main()
