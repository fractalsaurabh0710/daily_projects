#!/usr/bin/env python3
"""du-treemap - show what is eating a directory, as a squarified treemap.

    python3 du_treemap.py [path] [--top N] [--width C] [--height R]
    python3 du_treemap.py --selftest

Rectangle area is proportional to bytes on disk. The layout is the squarified
treemap of Bruls, Huizing & van Wijk (2000), which greedily packs items into
rows whose aspect ratios stay as close to 1 as it can manage.
"""
import os
import random
import sys

# ---------------------------------------------------------------- measuring

def tree_size(path):
    total = 0
    try:
        with os.scandir(path) as it:
            for e in it:
                try:
                    if e.is_symlink():
                        continue
                    total += tree_size(e.path) if e.is_dir() else e.stat().st_size
                except OSError:
                    pass
    except OSError:
        pass
    return total


def children(path):
    """[(label, bytes)] for the direct children of path, largest first."""
    out = []
    with os.scandir(path) as it:
        for e in it:
            try:
                if e.is_symlink():
                    continue
                is_dir = e.is_dir()
                size = tree_size(e.path) if is_dir else e.stat().st_size
            except OSError:
                continue
            if size:
                out.append((e.name + ("/" if is_dir else ""), size))
    out.sort(key=lambda kv: -kv[1])
    return out

# ---------------------------------------------------------------- squarify
# Rects are (x, y, w, h) in float units. Sizes are pre-scaled so that
# sum(sizes) == w * h, which makes every rect's area exactly its share.

def _row(sizes, x, y, dx, dy):
    w = sum(sizes) / dy
    rects, cur = [], y
    for s in sizes:
        rects.append((x, cur, w, s / w))
        cur += s / w
    return rects


def _col(sizes, x, y, dx, dy):
    h = sum(sizes) / dx
    rects, cur = [], x
    for s in sizes:
        rects.append((cur, y, s / h, h))
        cur += s / h
    return rects


def _lay(sizes, x, y, dx, dy):
    return _row(sizes, x, y, dx, dy) if dx >= dy else _col(sizes, x, y, dx, dy)


def _worst(sizes, x, y, dx, dy):
    ratios = []
    for _, _, w, h in _lay(sizes, x, y, dx, dy):
        if w <= 0 or h <= 0:
            return float("inf")
        ratios.append(max(w / h, h / w))
    return max(ratios)


def squarify(sizes, x, y, dx, dy):
    if not sizes:
        return []
    if len(sizes) == 1 or dx <= 0 or dy <= 0:
        return [(x, y, dx, dy)] if len(sizes) == 1 else []
    i = 1
    while i < len(sizes) and _worst(sizes[:i], x, y, dx, dy) >= _worst(sizes[: i + 1], x, y, dx, dy):
        i += 1
    head, tail = sizes[:i], sizes[i:]
    rects = _lay(head, x, y, dx, dy)
    if dx >= dy:
        used = sum(head) / dy
        rest = (x + used, y, dx - used, dy)
    else:
        used = sum(head) / dx
        rest = (x, y + used, dx, dy - used)
    return rects + squarify(tail, *rest)

# ---------------------------------------------------------------- rendering

COLORS = [67, 108, 137, 173, 139, 103, 72, 180, 66, 96, 131, 107, 109, 144]


def human(n):
    for unit in ("B", "K", "M", "G", "T"):
        if n < 1024 or unit == "T":
            return f"{n:.0f}{unit}" if unit == "B" or n >= 10 else f"{n:.1f}{unit}"
        n /= 1024


def render(items, cols, rows):
    total = sum(v for _, v in items)
    # Character cells are about twice as tall as wide, so lay the treemap out
    # in half-cell-wide units and stretch x back on the way out. Without this
    # every "square" comes out as a letterbox.
    ux = cols / 2.0
    sizes = [v / total * (ux * rows) for _, v in items]
    grid = [[(None, " ")] * cols for _ in range(rows)]
    for idx, ((name, val), (x, y, w, h)) in enumerate(zip(items, squarify(sizes, 0, 0, ux, rows))):
        c0, c1 = round(x * 2), round((x + w) * 2)
        r0, r1 = round(y), round(y + h)
        c1, r1 = min(c1, cols), min(r1, rows)
        if c1 - c0 < 1 or r1 - r0 < 1:
            continue
        color = COLORS[idx % len(COLORS)]
        for r in range(r0, r1):
            for c in range(c0, c1):
                grid[r][c] = (color, " ")
        room = c1 - c0 - 2
        # Prefer "name size"; if that will not fit, drop the size rather than
        # chopping a unit suffix off it and printing a meaningless number.
        label = f"{name} {human(val)}"
        if len(label) > room:
            label = name[:room]
        if len(label) >= 3 and r1 > r0:
            for k, ch in enumerate(label):
                grid[r0][c0 + 1 + k] = (color, ch)
    lines = []
    for row in grid:
        out, cur = [], object()
        for color, ch in row:
            if color != cur:
                out.append("\x1b[0m" if color is None else f"\x1b[48;5;{color}m\x1b[38;5;235m")
                cur = color
            out.append(ch)
        lines.append("".join(out) + "\x1b[0m")
    return "\n".join(lines)

# ---------------------------------------------------------------- selftest

def selftest():
    random.seed(7)
    for trial in range(200):
        n = random.randint(1, 30)
        vals = [random.random() ** 3 + 1e-3 for _ in range(n)]
        vals.sort(reverse=True)
        W, H = random.uniform(5, 120), random.uniform(5, 60)
        sizes = [v / sum(vals) * W * H for v in vals]
        rects = squarify(sizes, 0, 0, W, H)
        assert len(rects) == n, (n, len(rects))
        for want, (_, _, w, h) in zip(sizes, rects):
            assert abs(w * h - want) < 1e-6 * W * H, "area not proportional"
            assert w > 0 and h > 0
        assert abs(sum(w * h for _, _, w, h in rects) - W * H) < 1e-6 * W * H
        for i in range(n):
            ax, ay, aw, ah = rects[i]
            assert -1e-9 <= ax and ax + aw <= W + 1e-9
            assert -1e-9 <= ay and ay + ah <= H + 1e-9
            for j in range(i + 1, n):
                bx, by, bw, bh = rects[j]
                ox = min(ax + aw, bx + bw) - max(ax, bx)
                oy = min(ay + ah, by + bh) - max(ay, by)
                assert ox < 1e-9 or oy < 1e-9, f"rects {i},{j} overlap on trial {trial}"
    print("selftest ok: 200 layouts tile their rectangle exactly, no overlaps")


def main(argv):
    if "--selftest" in argv:
        return selftest()
    path, top, cols, rows = ".", 14, 78, 20
    rest = []
    i = 0
    while i < len(argv):
        if argv[i] in ("--top", "--width", "--height"):
            val = int(argv[i + 1])
            top, cols, rows = (val, cols, rows) if argv[i] == "--top" else (
                (top, val, rows) if argv[i] == "--width" else (top, cols, val))
            i += 2
        else:
            rest.append(argv[i])
            i += 1
    if rest:
        path = rest[0]
    items = children(path)
    if not items:
        print(f"nothing to show in {path}")
        return
    if len(items) > top:
        tail = sum(v for _, v in items[top:])
        items = items[:top] + [(f"+{len(items) - top} more", tail)]
    print(f"{os.path.abspath(path)} — {human(sum(v for _, v in items))}")
    print(render(items, cols, rows))


if __name__ == "__main__":
    main(sys.argv[1:])
