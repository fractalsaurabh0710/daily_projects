#!/usr/bin/env python3
"""astdiff - diff two Python files by meaning instead of by text.

A textual diff cannot tell a rewrite from a reformat. The parser can: comments
never reach the syntax tree at all, and docstrings and local variable names can
be normalised away. What survives that normalisation is the part that actually
changed behaviour.

Usage:  python3 astdiff.py old.py new.py      (no arguments: run the self-test)
"""

import ast
import copy
import sys

SCOPES = (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def definitions(tree):
    """Map qualified name -> node for every def and class, plus '<module>'."""
    found = {}

    def walk(parent, prefix):
        for node in parent.body:
            if isinstance(node, SCOPES):
                qual = prefix + node.name
                found[qual] = node
                walk(node, qual + ".")

    walk(tree, "")
    found["<module>"] = tree
    return found


def stub(body):
    """Replace nested defs with a placeholder so each scope is judged alone.

    Without this, editing one method would mark its class and its module changed
    too, and a 400-line file would report one useless 'everything moved'.
    """
    out = []
    for node in body:
        if isinstance(node, SCOPES):
            out.append(ast.Expr(ast.Constant(f"<{type(node).__name__} {node.name}>")))
        else:
            out.append(node)
    return out


def skeleton(node):
    """A copy of one scope: its own statements, its signature, no nested bodies."""
    clone = copy.deepcopy(node)
    clone.body = stub(clone.body)
    if not isinstance(clone, ast.Module):
        clone.name = ""  # the name is the dictionary key, not part of the body
    return clone


def strip_doc(body):
    if (body and isinstance(body[0], ast.Expr)
            and isinstance(body[0].value, ast.Constant)
            and isinstance(body[0].value.value, str)):
        return body[1:]
    return body


def local_names(node):
    """Names bound inside a function, which are therefore free to be renamed."""
    declared, bound = set(), set()
    for n in ast.walk(node):
        if isinstance(n, (ast.Global, ast.Nonlocal)):
            declared.update(n.names)
        elif isinstance(n, ast.Name) and isinstance(n.ctx, (ast.Store, ast.Del)):
            bound.add(n.id)
        elif isinstance(n, ast.arg):
            bound.add(n.arg)
        elif isinstance(n, ast.ExceptHandler) and n.name:
            bound.add(n.name)
        elif isinstance(n, (ast.Import, ast.ImportFrom)):
            bound.update((a.asname or a.name).split(".")[0] for a in n.names)
    return bound - declared


class Alpha(ast.NodeTransformer):
    """Rewrite locals to _v0, _v1, ... in order of first appearance."""

    def __init__(self, names):
        self.names = names
        self.seen = {}

    def _rename(self, name):
        if name not in self.names:
            return name
        return self.seen.setdefault(name, f"_v{len(self.seen)}")

    def visit_Name(self, node):
        node.id = self._rename(node.id)
        return node

    def visit_arg(self, node):
        node.arg = self._rename(node.arg)
        self.generic_visit(node)
        return node

    def visit_ExceptHandler(self, node):
        if node.name:
            node.name = self._rename(node.name)
        self.generic_visit(node)
        return node


def fingerprints(node):
    """(verbatim, docstring-blind, rename-blind) dumps of one scope."""
    base = skeleton(node)
    verbatim = ast.dump(base)
    base.body = strip_doc(base.body)
    blind_doc = ast.dump(base)
    if isinstance(node, FUNCS):
        base = Alpha(local_names(base)).visit(base)
    return verbatim, blind_doc, ast.dump(base)


def diff(old_src, new_src):
    old = {k: fingerprints(v) for k, v in definitions(ast.parse(old_src)).items()}
    new = {k: fingerprints(v) for k, v in definitions(ast.parse(new_src)).items()}
    verdicts = {}
    for name in sorted(set(old) | set(new)):
        if name not in new:
            verdicts[name] = "removed"
        elif name not in old:
            verdicts[name] = "added"
        else:
            (av, ad, al), (bv, bd, bl) = old[name], new[name]
            if av == bv:
                verdicts[name] = "unchanged"
            elif ad == bd:
                verdicts[name] = "docstring only"
            elif al == bl:
                verdicts[name] = "locals renamed"
            else:
                verdicts[name] = "changed"
    return verdicts


OLD = '''
"""A module."""
import os

LIMIT = 10

def total(values):
    """Add them up."""
    running = 0
    for value in values:
        running += value
    return running

def scale(xs, k):
    return [x * k for x in xs]

class Bag:
    def add(self, item):
        self.items.append(item)
    def drop(self, item):
        self.items.remove(item)
'''

NEW = '''
"""A module."""
import os

LIMIT = 10

def total(values):
    """Sum the values and return the result."""   # docstring reworded only
    running = 0
    for value in values:
        running += value
    return running

def scale(seq, factor):                            # locals renamed only
    return [item * factor for item in seq]

class Bag:
    def add(self, item):                           # genuinely different
        if item not in self.items:
            self.items.append(item)
    def size(self):                                # new method
        return len(self.items)
'''


def self_test():
    got = diff(OLD, NEW)
    expected = {
        "<module>": "unchanged",
        "total": "docstring only",
        "scale": "locals renamed",
        "Bag": "changed",
        "Bag.add": "changed",
        "Bag.drop": "removed",
        "Bag.size": "added",
    }
    assert got == expected, f"\n got: {got}\nwant: {expected}"

    # Reformatting and comments are invisible: the parser never sees them.
    assert diff("def f(a,b):return a+b", "def f(a, b):\n    # sum\n    return a + b") \
        == {"<module>": "unchanged", "f": "unchanged"}
    # A renamed global is not a local, so it is a real change.
    assert diff("X = 1", "Y = 1")["<module>"] == "changed"
    # Renaming is order-sensitive: swapping two parameters is not a rename.
    assert diff("def f(a, b): return a - b", "def f(b, a): return a - b")["f"] == "changed"
    print("all tests passed")


def main(argv):
    if len(argv) == 1:
        return self_test()
    if len(argv) != 3:
        sys.exit(__doc__.strip().splitlines()[-1])
    old, new = (open(p, encoding="utf-8").read() for p in argv[1:])
    verdicts = diff(old, new)
    for name, verdict in verdicts.items():
        if verdict != "unchanged":
            print(f"{verdict:>14}  {name}")
    quiet = sum(v == "unchanged" for v in verdicts.values())
    print(f"{'':>14}  ({quiet} of {len(verdicts)} scopes unchanged)")


if __name__ == "__main__":
    main(sys.argv)
