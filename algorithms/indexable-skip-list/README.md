# Indexable Skip List

A sorted multiset built from a skip list, with no rotations and no rebalancing —
balance comes from a coin flip per node. On top of the usual `insert`, `remove`
and `in`, every forward pointer also records its **span** (how many positions it
jumps), which makes the same structure an order-statistic one: `sl[k]` returns
the k-th smallest and `sl.rank(x)` counts the elements below `x`, both in
O(log n) without touching the bottom level.

## Run it

    python3 skip_list.py

Running the file executes its tests: 4,000 mixed insert/remove operations
mirrored against a plain sorted list, exhaustive `[]`/`rank` cross-checks, a
check that tower heights really follow the geometric distribution (≈50% reach
level 2, ≈25% level 3), and a measurement that lookup cost grows like log n.

## The non-obvious part

Maintaining spans through an insert is the whole trick. When a new node lands at
position `p`, a level-`i` pointer from `prev` splits into two: `prev → new` gets
span `p - pos(prev)`, and `new → old_next` gets `old_span - that + 1`. The `+ 1`
is there because every position after `p` has just shifted up by one. The same
formula happens to work for a pointer running off the end of the list, if you
define its span as the distance to one-past-the-last element. Levels above the
new node's height need no surgery at all — just `+= 1`, since they now step over
one extra node.
