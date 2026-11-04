# Splay Tree

A binary search tree that keeps no balance information whatsoever — no colours,
no heights, no ranks, not a single extra bit per node. The only rule is that
every access rotates the node it touched up to the root, and that is enough for
O(log n) amortised search, insert and delete.

## Run

    python3 main.py

No dependencies. The three tests print what they measured.

## What it demonstrates

The interesting claim isn't the amortised bound — it's that a splay tree can be
*cheaper than log n*, which no balanced tree can be, because a balanced tree
treats every key as equally likely.

- **Static optimality.** 2048 keys, with 2% of them taking 90% of the accesses:
  7.16 probes per access against 10.00 for a perfectly balanced tree. The hot
  keys drift to the top on their own. The test also computes the Shannon entropy
  of the access distribution (6.28 bits) and asserts the measured cost stays
  within the constant factor the static-optimality theorem promises — splay cost
  tracks the entropy of the workload, not the size of the tree.
- **Sequential access.** Inserting 1..n ascending leaves the tree as a literal
  path of n nodes, which is the worst case a BST has. An in-order scan over it
  costs 5.31, 5.32 and 5.32 probes per access at n = 5k, 20k and 80k — flat,
  while a balanced tree's 11.3 climbs to 15.3.

## Non-obvious bits

`splay` is the top-down Sleator–Tarjan version, built iteratively. That is not
style preference: a splay tree is *entitled* to be a 10,000-node path, so the
textbook recursive formulation blows the interpreter stack on exactly the input
the sequential test uses.

Cost is measured as the comparisons a plain BST search would make on the tree as
it currently stands (`_probe_depth`), taken before the splay rather than during
it, so the number is the honest depth of the key at the moment it was asked for.
