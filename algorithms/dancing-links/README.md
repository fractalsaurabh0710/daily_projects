# Dancing Links

Knuth's Algorithm X with the dancing-links representation: exact cover over a
sparse 0/1 matrix, where the matrix is a mesh of four-way doubly linked nodes
that unlinks and relinks itself as the search descends and backtracks.

## Run

    python3 dlx.py

It checks Knuth's six-row example matrix, counts N-queens solutions for n = 4..8
(2, 10, 4, 40, 92), and tiles a 4x4 board with two L-tetrominoes, an S and an I.

## The interesting part

Removing a node from a doubly linked list is `n.L.R = n.R; n.R.L = n.L` — and
the node's *own* `L` and `R` still point at its old neighbours. So undoing the
removal is `n.L.R = n.R.L = n`, with nothing saved and nothing copied. The
matrix shrinks as columns are covered and springs back exactly as it was on the
way out, which is what makes the backtracking free.

The second trick is optional columns. N-queens is not a natural exact cover:
every rank and file needs exactly one queen, but a diagonal needs *at most*
one. Diagonal columns are built into the matrix so covering a row still unlinks
them, but they are left out of the header ring, so Algorithm X never chooses to
branch on one and never insists it be filled.

Branching picks the column with the fewest remaining 1s, which is what keeps
8-queens at 92 solutions instead of a tour of the whole 64-row tree.
