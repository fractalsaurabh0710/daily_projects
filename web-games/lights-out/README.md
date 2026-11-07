# Lights Out

Classic 5×5 Lights Out: clicking a light toggles it and its four orthogonal
neighbours, and the board is cleared when every light is off. Single file, no
dependencies.

## Run

Open `index.html` in a browser.

"Hint" marks one cell from a fewest-press solution; "Show solution" lists the
whole set. `par` is the true minimum number of presses from the starting board,
not an estimate.

## The interesting part

Press order never matters and pressing a cell twice is a no-op, so a solution is
not a sequence but a *subset* of the 25 cells — i.e. a vector over GF(2). The
game is the linear system `A·x = b`, where `b` is the lit pattern and column `j`
of `A` is the plus-shape that pressing cell `j` toggles. Gaussian elimination mod
2 solves it in a few dozen lines.

What makes 5×5 particular is that `A` is singular: its null space is
2-dimensional. The two basis vectors are *quiet patterns* — press every cell in
one and the board comes back unchanged:

    . # # # .        # . # . #
    # . # . #        # # . # #
    # # . # #        # . # . #
    # . # . #        . . . . .
    . # # # .        # . # . #

So the rank is 23, which has two consequences the game leans on. Every solvable
board has exactly four solutions (one coset of the null space), which is why the
minimum-press answer can be found by brute force over just those four rather
than by search. And only 2²³ of the 2²⁵ possible boards are reachable at all —
one in four. Lighting cells at random would hand the player an impossible board
three times out of four, so the generator builds each puzzle by *pressing* from
a cleared board instead, which keeps it solvable by construction.

The test extraction (`node` on the inlined script, with a DOM stub) checks the
null space is 2-dimensional, that both basis vectors are genuinely quiet, that
the returned solution clears the board and is no longer than the other three in
its coset, and that sampling random boards finds ≈25% solvable.
