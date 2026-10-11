# Laser Mirrors

A 7x7 grid with a laser firing in from the left edge and a target pad somewhere on
the outside. Mirrors are already placed; you can only rotate them. Click a mirror to
flip it between `/` and `\` until the beam leaves the grid through the target.

## Run it

Open `index.html` in a browser. No build, no dependencies.

Run the engine's own tests with `node engine.js`.

## The interesting part

Generating a solvable puzzle by placing mirrors and then searching for a solution is
backwards and slow. Instead the generator *walks the beam*: it steps from the emitter
one cell at a time, sometimes dropping a mirror in the current cell (choosing an
orientation that keeps the beam on the board), and wherever the beam eventually
exits becomes the target. That layout is a solution by construction. The puzzle you
are handed is the same layout with roughly 60% of the mirrors flipped — so mirrors
are never added or moved, only rotated, which is exactly the move the player has.

`node engine.js` generates 2000 puzzles from a seeded PRNG and asserts for each one
that the construction solution hits the target, that the scrambled start does not,
and that the scramble preserved the mirror set.
