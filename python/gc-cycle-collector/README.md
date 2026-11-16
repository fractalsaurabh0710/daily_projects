# GC Cycle Collector

CPython's cycle detector, written in pure Python and checked against the real
one.

Reference counting cannot free a cycle: each node is kept alive by another node
in the same cycle, so no count ever reaches zero. CPython's collector resolves
this without tracing from global roots. It copies each candidate's real
reference count, then subtracts one for every reference arriving *from inside
the candidate set*. Whatever is left over came from outside, so an object with
a non-zero leftover is a root; anything reachable from a root survives, and the
rest is garbage no matter how high its raw reference count looked.

Nodes are plain lists, so each graph node is exactly one GC-tracked object with
no hidden instance dict to muddle the counts.

## Run

    python3 gc_cycles.py

Three checks: a closed 3-cycle (raw refcount 1 each, external refs 0 each, all
three condemned); 400 random digraphs where the refcount verdict is compared
against straightforward reachability from a live root; and 20 graphs where the
prediction is compared against what `gc.collect()` actually reports.

## The part that took the most care

Writing this in Python means the measuring apparatus is itself a reference
holder. `sys.getrefcount(o)` counts the candidate list's slot, the loop
variable, and its own argument — three references CPython's collector would
never see — so the code measures that overhead with a probe built the same way
rather than hardcoding 3.

The second surprise is that the prediction does *not* equal `gc.collect()`'s
return value. Across the 400 random graphs, 1576 of 9600 nodes are unreachable,
but only 235 of those need the cycle collector: the other 1341 have no incoming
reference once the generation list lets go, so refcounting frees them
immediately and cascades, and `gc.collect()` never sees them. Matching the real
collector therefore meant peeling zero-in-degree nodes off the unreachable set
until only the cyclic core remained — which is what the assertion compares.
