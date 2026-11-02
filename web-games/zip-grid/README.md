# Zip Grid

A 6×6 path puzzle. Drag from the cell marked **1** to the last number, passing
through the numbers in order and filling every cell exactly once. Dragging back
over the line rewinds it, so a wrong turn costs nothing.

## Run

Open `index.html` in a browser. `node test.js` checks the generator.

## How the puzzles are made

Generating a random Hamiltonian path by search is miserable — most partial paths
strand a cell and the backtracking is heavy. So this never searches. It starts
from the boustrophedon snake, which already visits every cell, and then applies
a few thousand *backbite* moves: take one end of the path, pick a random grid
neighbour of it, and reverse the tail of the path behind that neighbour. The
result is still a path, still simple, still spanning — the move cannot produce
anything invalid, so every intermediate state is a Hamiltonian path and the walk
mixes them.

The numbers are then placed on cells along that path, five to eight cells apart.
The solution therefore exists before the puzzle does, and `test.js` checks the
property the game relies on: walking the generated path meets the numbers in
exactly the order the game demands while you drag.

Nice side effect of the seed being a snake: cell 0 is its start, but after
backbiting, 300 seeds produce 36 distinct start cells — every cell on the board.
