#!/usr/bin/env python3
"""indent-sniff - infer the indentation style of a text file.

The naive approach (take the most common indent width) is wrong, and so is
taking the most common *delta* between consecutive line indents: continuation
lines aligned under an open paren put arbitrary widths into both histograms.

What actually identifies the width is divisibility. Every real indent is a
multiple of the unit, so the unit is close to the GCD of the observed indents
-- but a strict GCD is destroyed by a single aligned continuation line, and it
also collapses to 2 for any file that happens to contain one 2-space oddity.
So: score each candidate by the share of indents it divides, and take the
LARGEST candidate that clears a threshold. Smaller units trivially divide more
(2 divides everything 4 does), which is why largest-first is the right order.

Usage:  indent-sniff.py FILE [FILE ...]
        indent-sniff.py --selftest
"""

import sys
from collections import Counter

CANDIDATES = (8, 6, 4, 3, 2)  # tried largest-first; see module docstring
COVERAGE = 0.90               # share of indents a width must divide


def leading(line):
    """(tabs, spaces, is_blank) for the leading whitespace of one line."""
    tabs = spaces = 0
    i = 0
    while i < len(line) and line[i] in " \t":
        if line[i] == "\t":
            tabs += 1
        else:
            spaces += 1
        i += 1
    return tabs, spaces, i == len(line)


def pick_width(widths):
    """Largest candidate dividing >= COVERAGE of the indents."""
    if not widths:
        return None, {}
    n = len(widths)
    cov = {w: sum(1 for x in widths if x % w == 0) / n for w in CANDIDATES}
    for w in CANDIDATES:
        if cov[w] >= COVERAGE:
            return w, cov
    # Nothing clears the bar: fall back to the best coverage, largest on ties.
    return max(CANDIDATES, key=lambda w: (cov[w], w)), cov


def sniff(text):
    tab_lines = 0
    mixed = 0
    space_widths = []
    for raw in text.splitlines():
        tabs, spaces, blank = leading(raw)
        if blank or (tabs == 0 and spaces == 0):
            continue
        if tabs and spaces:
            mixed += 1
        if tabs:
            tab_lines += 1
        else:
            space_widths.append(spaces)

    indented = tab_lines + len(space_widths)
    if indented == 0:
        return {"style": "none", "width": None, "conf": 0.0,
                "indented": 0, "mixed": 0, "depth": 0}

    if tab_lines > len(space_widths):
        return {"style": "tabs", "width": 1, "conf": tab_lines / indented,
                "indented": indented, "mixed": mixed,
                "depth": max((t for t, _, _ in
                              (leading(l) for l in text.splitlines())), default=0)}

    width, cov = pick_width(space_widths)
    return {"style": "spaces", "width": width, "conf": cov.get(width, 0.0),
            "indented": indented, "mixed": mixed,
            "depth": max(space_widths) // width if width else 0}


def report(paths):
    print(f"{'file':<44} {'style':<7} {'unit':>4} {'conf':>5} "
          f"{'indent':>6} {'depth':>5} {'mixed':>5}")
    for p in paths:
        try:
            with open(p, "r", encoding="utf-8", errors="replace") as fh:
                r = sniff(fh.read())
        except OSError as e:
            print(f"{p:<44} -- {e.strerror}")
            continue
        unit = "tab" if r["style"] == "tabs" else (r["width"] or "-")
        name = p if len(p) <= 44 else "..." + p[-41:]
        print(f"{name:<44} {r['style']:<7} {str(unit):>4} {r['conf']:>5.2f} "
              f"{r['indented']:>6} {r['depth']:>5} {r['mixed']:>5}")


def selftest():
    def body(unit, levels=(1, 2, 3, 2, 1)):
        return "\n".join(" " * (unit * d) + "x" for d in levels)

    for unit in (2, 3, 4, 8):
        got = sniff(body(unit))
        assert got["style"] == "spaces" and got["width"] == unit, (unit, got)

    # One continuation line aligned at 13 columns must not drag 4 down to 1/2.
    noisy = body(4) + "\n" + " " * 13 + "aligned"
    assert sniff(noisy)["width"] == 4, sniff(noisy)

    # Tabs win when they are the majority.
    assert sniff("\tx\n\t\ty\n  z")["style"] == "tabs"

    # A file indented only at level 1 with unit 4: 8 divides nothing, so 4.
    assert sniff("    a\n    b\n    c")["width"] == 4

    # 2-space file: 4 covers only half the indents, so 2 wins.
    assert sniff(body(2))["width"] == 2

    # No indentation at all.
    assert sniff("a\nb\n")["style"] == "none"

    # Mixed tabs+spaces on one line is counted, not silently merged.
    assert sniff(" \tx\n    y\n    z\n    w")["mixed"] == 1

    print("selftest ok")


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__.strip().splitlines()[-2].strip(), file=sys.stderr)
        sys.exit(2)
    if args[0] == "--selftest":
        selftest()
    else:
        report(args)
