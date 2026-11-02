# Tilt Maze

An 8×8 sliding puzzle: pick a direction and the ball keeps going until a wall or
the edge of the board stops it. Get it onto the ring. Arrow keys or WASD, or the
on-screen pad; "New level" generates another one.

## Run

Open `index.html` in a browser. No build, no dependencies.

The logic also runs headless — `node game.js` executes the test suite, which
checks sliding, the move graph, and that 200 generated levels are solvable with
the displayed par being the true shortest solution.

## The interesting part

The ball can only come to rest where something blocks it, so most empty cells are
not valid stopping places at all — on a board with no walls at all the ball can
only ever occupy nine cells, no matter how long you play. That makes picking a
goal by choosing a random empty cell wrong: you'd often hand the player a target
they can never land on.

So the generator scatters walls, runs a BFS over resting places, and takes the
goal from the BFS output — the cell that is *furthest* from the start. Every level
is therefore solvable by construction, and par is the real shortest solution
rather than an estimate.
