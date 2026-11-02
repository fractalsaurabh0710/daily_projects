#!/usr/bin/env python3
"""Find duplicate files by reading as few bytes as possible.

Three sieves, cheapest first: size, then a 4 KiB head hash, then the
whole file. Only files that survive a stage reach the next one, so the
full read -- the expensive part -- happens for near-certain duplicates
only. The tool reports how many bytes it actually read.
"""

import argparse
import hashlib
import os
import sys
from collections import defaultdict

HEAD = 4096
CHUNK = 1 << 20

bytes_read = 0


def digest(path, limit=None):
    """blake2b of the file, or of its first `limit` bytes."""
    global bytes_read
    h = hashlib.blake2b(digest_size=16)
    remaining = limit if limit is not None else float("inf")
    with open(path, "rb") as fh:
        while remaining > 0:
            block = fh.read(int(min(CHUNK, remaining)))
            if not block:
                break
            remaining -= len(block)
            bytes_read += len(block)
            h.update(block)
    return h.digest()


def scan(roots, min_size):
    """Every regular file under `roots`, as (size, path). Symlinks skipped."""
    seen = set()
    for root in roots:
        if os.path.isfile(root):
            walk = [(os.path.dirname(root) or ".", [], [os.path.basename(root)])]
        else:
            walk = os.walk(root)
        for dirpath, dirnames, filenames in walk:
            dirnames[:] = [d for d in dirnames if not os.path.islink(os.path.join(dirpath, d))]
            for name in filenames:
                path = os.path.join(dirpath, name)
                if os.path.islink(path):
                    continue
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                if not os.path.isfile(path) or st.st_size < min_size:
                    continue
                key = (st.st_dev, st.st_ino)
                if key in seen:          # same file reached twice (hard link / overlapping roots)
                    continue
                seen.add(key)
                yield st.st_size, path


def sieve(files):
    """files: iterable of (size, path) -> list of (size, [paths]) duplicate groups."""
    by_size = defaultdict(list)
    for size, path in files:
        by_size[size].append(path)

    survivors = []
    for size, paths in by_size.items():
        if len(paths) > 1:
            survivors.append((size, paths))

    by_head = defaultdict(list)
    for size, paths in survivors:
        if size <= HEAD:
            by_head[(size, b"whole")].extend(paths)   # a short file's head IS the file
            continue
        for path in paths:
            try:
                by_head[(size, digest(path, HEAD))].append(path)
            except OSError:
                pass

    groups = []
    for (size, head), paths in by_head.items():
        if len(paths) < 2:
            continue
        by_full = defaultdict(list)
        for path in paths:
            try:
                by_full[digest(path)].append(path)
            except OSError:
                pass
        for dupes in by_full.values():
            if len(dupes) > 1:
                groups.append((size, sorted(dupes)))
    groups.sort(key=lambda g: (-g[0] * (len(g[1]) - 1), g[1][0]))
    return groups


def human(n):
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if n < 1024 or unit == "TiB":
            return "%.0f %s" % (n, unit) if unit == "B" else "%.1f %s" % (n, unit)
        n /= 1024


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("paths", nargs="*", default=["."], help="files or directories to scan")
    ap.add_argument("--min-size", type=int, default=1, help="ignore files smaller than this (bytes)")
    ap.add_argument("--selftest", action="store_true", help="run the built-in tests and exit")
    args = ap.parse_args(argv)

    if args.selftest:
        return selftest()

    files = list(scan(args.paths or ["."], args.min_size))
    total = sum(size for size, _ in files)
    groups = sieve(files)

    wasted = 0
    for size, paths in groups:
        wasted += size * (len(paths) - 1)
        print("%s x%d" % (human(size), len(paths)))
        for path in paths:
            print("    " + path)
        print()

    print("%d files, %s on disk" % (len(files), human(total)))
    print("%d duplicate group%s, %s reclaimable"
          % (len(groups), "" if len(groups) == 1 else "s", human(wasted)))
    share = (100.0 * bytes_read / total) if total else 0.0
    print("read %s to find them (%.1f%% of the data)" % (human(bytes_read), share))
    return 0


def selftest():
    import tempfile
    global bytes_read

    with tempfile.TemporaryDirectory() as tmp:
        def write(name, data):
            path = os.path.join(tmp, name)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as fh:
                fh.write(data)
            return path

        body = os.urandom(200_000)
        write("a.bin", body)
        write("sub/b.bin", body)                              # exact duplicate
        write("c.bin", body[:-1] + bytes([body[-1] ^ 1]))     # same size, same head, last byte differs
        write("d.bin", os.urandom(200_000))                   # same size, different head
        write("e.txt", b"hi")
        write("f.txt", b"hi")                                 # duplicate shorter than HEAD
        write("g.txt", b"ho")

        bytes_read = 0
        groups = sieve(scan([tmp], 1))
        found = {frozenset(os.path.basename(p) for p in paths) for _, paths in groups}
        assert found == {frozenset({"a.bin", "b.bin"}), frozenset({"e.txt", "f.txt"})}, found

        # a, b, c and d share a size, so all four get a head read; only the
        # three with a matching head are then read in full -- d never is.
        # The three 2-byte files skip the head stage and are read whole.
        assert bytes_read == 4 * HEAD + 3 * 200_000 + 3 * 2, bytes_read

        # Groups are ordered by bytes reclaimable, largest first.
        assert [g[0] for g in groups] == [200_000, 2]

        # A file listed twice, or reached through two overlapping roots, is one file.
        assert len(list(scan([tmp, tmp], 1))) == 7
        assert sieve(scan([os.path.join(tmp, "a.bin")], 1)) == []

        # min-size skips the small pair entirely.
        assert len(sieve(scan([tmp], 1000))) == 1

    print("all tests passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
