# Aho-Corasick

Find every occurrence of every pattern in a text, in one pass, with one table
lookup per character. Pure standard library.

## Run

    python3 aho_corasick.py

It runs its tests (hand-picked overlap cases plus 400 randomised cross-checks
against naive `str.find` search) and then prints the matches for a small
example, each lined up under where it occurs.

## Use

```python
ac = AhoCorasick(["he", "she", "his", "hers"])
ac.matches("ushers")        # [(1, 'she'), (2, 'he'), (2, 'hers')]
list(ac.find_all("ushers")) # (end_index_exclusive, pattern_index) pairs
```

## The interesting part

Two things make the scan a plain table walk rather than a search with backtracking.

The BFS that computes failure links also *densifies* the trie: after it runs,
every node has an edge for every character seen anywhere in the patterns, copied
down from its failure node. That works only because the BFS visits nodes in
depth order, and a node's failure link always points somewhere shallower — so by
the time a node is processed, the node it borrows from is already complete.

The second is that matching and reporting are separate. A failure link also
inherits matches: `he` is a suffix of `she`, so landing on the node for `she`
has to report `he` as well. Each node stores a link straight to the nearest
failure-ancestor that ends a pattern, so reporting skips the nodes that end
nothing. That is what keeps the cost at O(text + matches) rather than O(text ×
patterns) — overlapping output is the only thing that can make it slow, and only
in proportion to how much output there is.
