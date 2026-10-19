# AST Semantic Diff

A textual diff cannot tell a rewrite from a reformat. `astdiff.py` compares two
Python files through their syntax trees instead, and reports one verdict per
scope: `unchanged`, `docstring only`, `locals renamed`, `changed`, `added` or
`removed`.

Three fingerprints are taken of every scope — verbatim, with the docstring
dropped, and with local variables rewritten to `_v0, _v1, …` in order of first
appearance — and the first one that matches decides the verdict. Comments need
no handling at all: the parser discards them before the tree exists.

## Run it

```
python3 astdiff.py old.py new.py   # report the differences
python3 astdiff.py                 # run the self-test
```

## The non-obvious part

Each scope is fingerprinted on its own statements only, with nested defs
replaced by a placeholder naming them. Without that, editing one method would
mark its class and its whole module changed too, and the report for a large
file would collapse into "everything moved". The placeholder still carries the
name, so adding or deleting a method does show up on the enclosing scope.

Alpha-renaming is positional, not a set comparison, so swapping two parameters
is correctly reported as a change rather than a rename — and only function
locals are renamed, since module globals and class attributes are API.
