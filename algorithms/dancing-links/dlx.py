"""Dancing Links (Knuth's Algorithm X) over a sparse 0/1 matrix.

Exact cover: pick a set of rows so that every *primary* column holds exactly
one 1. Optional (secondary) columns may hold at most one. The trick is that
removing a node from a doubly linked list leaves the node's own pointers
intact, so the same node can splice itself back in on backtrack -- the matrix
unbuilds and rebuilds itself with no allocation and no copying.
"""


class Node:
    __slots__ = ("L", "R", "U", "D", "col", "row")

    def __init__(self, row=-1):
        self.L = self.R = self.U = self.D = self
        self.col = None
        self.row = row


class Column(Node):
    __slots__ = ("size", "name", "optional")

    def __init__(self, name, optional=False):
        super().__init__()
        self.col, self.size, self.name, self.optional = self, 0, name, optional


class DLX:
    def __init__(self, names, optional=()):
        self.head = Column("__head__")
        self.cols = {}
        for name in names:
            c = Column(name, name in optional)
            self.cols[name] = c
            if not c.optional:              # optional columns stay off the
                c.L, c.R = self.head.L, self.head   # header ring, so Algorithm X
                self.head.L.R = self.head.L = c     # never tries to satisfy them
        self.rows = []

    def add_row(self, label, names):
        """Add one row; `names` are the columns holding a 1."""
        idx = len(self.rows)
        self.rows.append(label)
        first = None
        for name in names:
            c = self.cols[name]
            n = Node(idx)
            n.col, n.U, n.D = c, c.U, c
            c.U.D = c.U = n
            c.size += 1
            if first is None:
                first = n
            else:
                n.L, n.R = first.L, first
                first.L.R = first.L = n
        return idx

    @staticmethod
    def _cover(c):
        c.R.L, c.L.R = c.L, c.R
        i = c.D
        while i is not c:
            j = i.R
            while j is not i:
                j.D.U, j.U.D = j.U, j.D
                j.col.size -= 1
                j = j.R
            i = i.D

    @staticmethod
    def _uncover(c):
        i = c.U
        while i is not c:
            j = i.L
            while j is not i:
                j.col.size += 1
                j.D.U = j.U.D = j
                j = j.L
            i = i.U
        c.R.L = c.L.R = c

    def solve(self):
        """Yield solutions, each a list of row labels."""
        yield from self._search([])

    def _search(self, stack):
        h = self.head
        if h.R is h:
            yield [self.rows[r] for r in stack]
            return
        best, c = None, h.R          # S-heuristic: branch on the column with
        while c is not h:            # the fewest 1s, which keeps the tree thin
            if best is None or c.size < best.size:
                best = c
            c = c.R
        if best.size == 0:
            return
        self._cover(best)
        r = best.D
        while r is not best:
            stack.append(r.row)
            j = r.R
            while j is not r:
                self._cover(j.col)
                j = j.R
            yield from self._search(stack)
            j = r.L
            while j is not r:
                self._uncover(j.col)
                j = j.L
            stack.pop()
            r = r.D
        self._uncover(best)


def n_queens(n):
    """Rows and files are primary (exactly one queen); diagonals optional."""
    primary = [f"r{i}" for i in range(n)] + [f"f{j}" for j in range(n)]
    optional = [f"a{k}" for k in range(2 * n - 1)] + [f"b{k}" for k in range(2 * n - 1)]
    d = DLX(primary + optional, optional=set(optional))
    for i in range(n):
        for j in range(n):
            d.add_row((i, j), [f"r{i}", f"f{j}", f"a{i + j}", f"b{i - j + n - 1}"])
    return d


def pentomino_board(rows, cols, pieces):
    """Tile a rows x cols board; each cell and each piece used exactly once."""
    names = [f"c{r},{c}" for r in range(rows) for c in range(cols)] + list(pieces)
    d = DLX(names)
    for name, cells in pieces.items():
        seen = set()
        for _ in range(4):                       # 4 rotations x 2 reflections
            cells = [(c, -r) for r, c in cells]
            for shape in (cells, [(r, -c) for r, c in cells]):
                lr, lc = min(r for r, _ in shape), min(c for _, c in shape)
                norm = tuple(sorted((r - lr, c - lc) for r, c in shape))
                if norm in seen:
                    continue
                seen.add(norm)
                h, w = max(r for r, _ in norm) + 1, max(c for _, c in norm) + 1
                for dr in range(rows - h + 1):
                    for dc in range(cols - w + 1):
                        placed = [(r + dr, c + dc) for r, c in norm]
                        d.add_row((name, placed),
                                  [name] + [f"c{r},{c}" for r, c in placed])
    return d


if __name__ == "__main__":
    tiny = DLX("ABCDEFG")                    # Knuth's example matrix
    for label, cs in [("r0", "CEF"), ("r1", "ADG"), ("r2", "BCF"),
                      ("r3", "AD"), ("r4", "BG"), ("r5", "DEG")]:
        tiny.add_row(label, cs)
    assert sorted(sorted(s) for s in tiny.solve()) == [["r0", "r3", "r4"]]

    for n, expected in [(4, 2), (5, 10), (6, 4), (7, 40), (8, 92)]:
        assert sum(1 for _ in n_queens(n).solve()) == expected, n
        print(f"{n}-queens: {expected} solutions")

    L = {(0, 0), (1, 0), (2, 0), (2, 1)}
    pieces = {"L": L, "J": L,                       # same shape, two copies
              "S": {(0, 1), (0, 2), (1, 0), (1, 1)},
              "I": {(0, 0), (0, 1), (0, 2), (0, 3)}}
    sols = list(pentomino_board(4, 4, pieces).solve())
    assert len(sols) == 48 and all(len(s) == 4 for s in sols)
    grid = [["."] * 4 for _ in range(4)]
    for name, cells in sols[0]:
        for r, c in cells:
            grid[r][c] = name
    print(f"\n4x4 tetromino tiling, L+L+S+I: {len(sols)} solutions "
          f"({len(sols) // 2} up to swapping the two Ls). One of them:")
    print("\n".join(" ".join(row) for row in grid))
