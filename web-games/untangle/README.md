# Untangle

Drag the dots until no two lines cross. Red edges are the ones still tangled;
when everything is green the puzzle is solved.

## Run it

Open `index.html` in a browser. No build step, no dependencies.

`node test.js` runs the correctness tests.

## How the puzzles are made

Every puzzle is solvable, and not by luck. The generator scatters points in the
square, sorts all node pairs by distance, and adds each edge only if it crosses
no edge already placed — a greedy planar drawing. That drawing is kept as the
answer, then the nodes are thrown onto a circle in random order. Scrambling
moves positions and nothing else, so the planar layout the generator found is
still a valid solution to the tangle the player is handed.

The test exercises exactly that claim: it generates 100 puzzles, puts the nodes
back on the generator's own coordinates, and asserts the crossing count is zero
every time.

The one subtlety in the geometry is that two edges meeting at a shared node are
*not* a crossing, so the orientation test has to reject that case explicitly
before looking at the signs — otherwise the collinear-at-an-endpoint degeneracy
reports a crossing that no player could ever remove.
