"""A deterministic call-tree profiler in ~150 lines, built on sys.setprofile.

cProfile gives you a flat table: each function with its cumulative time, callers
smeared together. This keeps the *shape* of the run instead -- who called whom,
and where the time went along each path -- and prints it as an indented tree.

Usage:
    with CallTreeProfiler() as p:
        your_code()
    p.report()
"""

import sys
import time
from dataclasses import dataclass, field


@dataclass
class Node:
    """One call site: a function as reached by one particular path."""

    name: str
    calls: int = 0
    total: float = 0.0           # wall time inside this node, including children
    children: dict = field(default_factory=dict)

    def child(self, name):
        node = self.children.get(name)
        if node is None:
            node = self.children[name] = Node(name)
        return node

    @property
    def own(self):
        """Time spent in this frame itself, excluding nested calls."""
        return self.total - sum(c.total for c in self.children.values())


def _label(frame_or_fn, is_c):
    if is_c:
        mod = getattr(frame_or_fn, "__module__", None) or "builtins"
        return f"{mod}.{frame_or_fn.__name__} [C]"
    code = frame_or_fn.f_code
    return f"{code.co_name} ({code.co_filename.rsplit('/', 1)[-1]}:{code.co_firstlineno})"


class CallTreeProfiler:
    def __init__(self, clock=time.perf_counter):
        self.clock = clock
        self.root = Node("<root>")
        self._stack = []        # [(node, entry_time)]

    # -- profiling hook -------------------------------------------------
    def _hook(self, frame, event, arg):
        # The hook itself is not profiled (CPython disables tracing inside it),
        # so the only skew is the cost of these few lines per call.
        now = self.clock()
        if event == "call" or event == "c_call":
            parent = self._stack[-1][0] if self._stack else self.root
            node = parent.child(_label(arg if event == "c_call" else frame,
                                       event == "c_call"))
            node.calls += 1
            self._stack.append((node, now))
        elif event in ("return", "c_return", "c_exception"):
            if self._stack:
                node, started = self._stack.pop()
                node.total += now - started

    # -- lifecycle ------------------------------------------------------
    def __enter__(self):
        self._stack.clear()
        sys.setprofile(self._hook)
        return self

    def __exit__(self, *exc):
        sys.setprofile(None)
        # The frame that called __exit__ never gets its 'return' event.
        now = self.clock()
        while self._stack:
            node, started = self._stack.pop()
            node.total += now - started
        return False

    # -- reporting ------------------------------------------------------
    def report(self, min_pct=0.5, max_depth=None, out=sys.stdout):
        total = sum(c.total for c in self.root.children.values())
        if not total:
            print("nothing profiled", file=out)
            return
        print(f"{'cumulative':>10} {'self':>8} {'calls':>7}  call tree "
              f"(>{min_pct}% of {total * 1000:.1f}ms)", file=out)
        self._walk(self.root, total, 0, min_pct, max_depth, out)

    def _walk(self, node, total, depth, min_pct, max_depth, out):
        if max_depth is not None and depth >= max_depth:
            hidden = sum(1 for _ in self._descendants(node))
            if hidden:
                print(f"{'':28}  {'  ' * depth}... {hidden} deeper "
                      f"call sites elided", file=out)
            return
        for child in sorted(node.children.values(), key=lambda n: -n.total):
            pct = 100 * child.total / total
            if pct < min_pct:
                continue
            bar = "#" * max(1, round(pct / 5))
            print(f"{child.total * 1000:9.2f}ms {child.own * 1000:7.2f}ms "
                  f"{child.calls:7d}  {'  ' * depth}{child.name} "
                  f"{bar} {pct:.1f}%", file=out)
            self._walk(child, total, depth + 1, min_pct, max_depth, out)

    def _descendants(self, node):
        for child in node.children.values():
            yield child
            yield from self._descendants(child)


# ---------------------------------------------------------------- demo ----
def fib(n):
    return n if n < 2 else fib(n - 1) + fib(n - 2)


def build_words(n):
    return ["".join(sorted(str(i * 7919))) for i in range(n)]


def count_pairs(words):
    seen = {}
    for w in words:
        seen[w] = seen.get(w, 0) + 1
    return sum(v * (v - 1) // 2 for v in seen.values())


def workload():
    fib(18)
    words = build_words(4000)
    return count_pairs(words)


def _self_test():
    """The tree must reproduce the call counts we can compute by hand."""
    with CallTreeProfiler() as p:
        fib(10)

    # fib(10) makes 177 calls in total: 1 + the number of recursive calls.
    def count(n, memo={}):
        if n < 2:
            return 1
        if n not in memo:
            memo[n] = 1 + count(n - 1) + count(n - 2)
        return memo[n]

    def total_calls(node):
        return node.calls + sum(total_calls(c) for c in node.children.values())

    top = next(iter(p.root.children.values()))
    assert top.name.startswith("fib "), top.name
    assert total_calls(top) == count(10), (total_calls(top), count(10))
    assert top.total >= top.own >= 0
    # Depth of the tree is the recursion depth of fib(10), which is 10.
    def depth(node):
        return 1 + max((depth(c) for c in node.children.values()), default=0)
    assert depth(top) == 10, depth(top)
    print(f"self-test ok: {count(10)} calls, depth 10")


if __name__ == "__main__":
    _self_test()
    print()
    with CallTreeProfiler() as prof:
        workload()
    prof.report(max_depth=4)
