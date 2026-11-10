# C3 Linearization

CPython computes `type.__mro__` with the C3 algorithm. C3 is short enough to
write out by hand, so this writes it out and then checks the result against the
real thing: random class hierarchies get linearized here and compared, name for
name, with `cls.__mro__`.

## Run

```
python3 mro.py
```

It prints how many random hierarchies linearized, how many had no valid MRO,
and the longest chain it found. Every case is cross-checked against CPython.

## The interesting part

The merge step is one rule — take the first head that appears in no other
sequence's tail — and the whole of Python's inheritance ordering falls out of
it. The direct base list is fed in as a sequence of its own alongside the bases'
MROs; that single extra sequence is what makes `class Z(X, Y)` binding, so no
amount of ancestry can push `Y` ahead of `X`.

The failure case is just the merge running out of candidates: when every
remaining head is waiting on something else, the bases are asking for
contradictory orders and there is no linearization at all. CPython raises
`TypeError` at exactly that point, which makes refusal testable too — the
comparison asserts both implementations reject the same hierarchies, not only
that they agree on the ones that work.

How often that happens is the surprise: with 1-3 bases drawn at random from
earlier classes, about two thirds of hierarchies have no valid MRO. Consistent
multiple inheritance is the rare case, not the default one.
