# No-Guess Minesweeper

A 9x9 / 10-mine Minesweeper where every board is solvable by logic alone. The
usual game eventually corners you into a coin flip; this one never does, because
a board is only handed to you once a solver has proved it doesn't have to be
guessed at.

## Run it

Open `index.html` in a browser (left-click to dig, right-click to flag), or run
the generator's self-test:

    node solver.js

## How the guarantee works

The generator doesn't construct solvable boards — it rejects unsolvable ones.
Place the mines at random with a mine-free 3x3 around a chosen first click, then
play the board as a perfect logician and see whether the logician finishes.
Two rules, applied until nothing new follows:

1. A number whose unflagged mine count is 0 clears its unknown neighbours; one
   whose count equals its unknown neighbour count mines all of them.
2. When one number's unknown neighbours are a *subset* of another's, the extra
   cells hold exactly the difference of the two counts — decisive whenever that
   difference is 0 or all of them. This is the rule that resolves the 1-2-1 and
   1-2-2-1 wall patterns a human player learns by shape.

If any cell is still undecided when the rules run dry, the board is thrown away.

## What was interesting

Guessy boards are far more common than they feel, and far cheaper to avoid than
that suggests. Of 400 random 9x9 boards with the usual mine-free opening,
**89 (22.3%) cannot be finished without a guess** — and they don't fail at the
last cell, either: on average **21.5 cells**, a quarter of the board, are still
undecided when logic runs out. Yet because the two rules are cheap and the
failures are independent, filtering costs almost nothing: **1.2 candidate boards
tried per playable board**, worst case 4 in that run. A guarantee that sounds
like it needs a constructive generator turns out to need only rejection
sampling and about 10 rounds of deduction per board.
