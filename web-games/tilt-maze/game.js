// Tilt Maze — the ball slides until something stops it.
// Pure logic first (testable in Node), DOM wiring at the bottom.

const SIZE = 8;
const DIRS = { up: [-1, 0], down: [1, 0], left: [0, -1], right: [0, 1] };

// Slide from `pos` in `dir` until the next cell is a wall or off the board.
function slide(grid, pos, dir) {
  const [dr, dc] = dir;
  let [r, c] = pos;
  for (;;) {
    const nr = r + dr, nc = c + dc;
    if (nr < 0 || nr >= SIZE || nc < 0 || nc >= SIZE) break;
    if (grid[nr][nc]) break;
    r = nr; c = nc;
  }
  return [r, c];
}

// BFS over resting places. The move graph is sparse: a cell is only a node if
// some slide can come to rest on it.
function reachable(grid, start) {
  const key = ([r, c]) => r + ',' + c;
  const dist = new Map([[key(start), 0]]);
  const queue = [start];
  for (let i = 0; i < queue.length; i++) {
    const pos = queue[i], d = dist.get(key(pos));
    for (const dir of Object.values(DIRS)) {
      const next = slide(grid, pos, dir);
      if (!dist.has(key(next))) {
        dist.set(key(next), d + 1);
        queue.push(next);
      }
    }
  }
  return dist;
}

// Scatter walls, then let BFS choose the goal. Picking an empty cell at random
// would usually pick one the ball can never stop on.
function generate(minPar = 6, rand = Math.random) {
  for (let attempt = 0; attempt < 500; attempt++) {
    const grid = Array.from({ length: SIZE }, () =>
      Array.from({ length: SIZE }, () => (rand() < 0.2 ? 1 : 0)));
    const start = [Math.floor(rand() * SIZE), Math.floor(rand() * SIZE)];
    if (grid[start[0]][start[1]]) continue;

    const dist = reachable(grid, start);
    let best = null, par = 0;
    for (const [k, d] of dist) {
      if (d > par) { par = d; best = k.split(',').map(Number); }
    }
    if (par >= minPar) return { grid, start, goal: best, par };
  }
  throw new Error('generator gave up');
}

// ---------------------------------------------------------------- browser ---

if (typeof document !== 'undefined') {
  const boardEl = document.getElementById('board');
  const statusEl = document.getElementById('status');
  let level, ball, moves, won;

  function newLevel() {
    level = generate();
    ball = level.start;
    moves = 0;
    won = false;
    draw();
  }

  function draw() {
    boardEl.innerHTML = '';
    for (let r = 0; r < SIZE; r++) {
      for (let c = 0; c < SIZE; c++) {
        const cell = document.createElement('div');
        cell.className = 'cell';
        if (level.grid[r][c]) cell.classList.add('wall');
        if (r === level.goal[0] && c === level.goal[1]) cell.classList.add('goal');
        if (r === ball[0] && c === ball[1]) cell.classList.add('ball');
        boardEl.appendChild(cell);
      }
    }
    statusEl.textContent = won
      ? `Solved in ${moves} ${moves === 1 ? 'move' : 'moves'} (par ${level.par}).`
      : `Moves: ${moves} · par ${level.par}`;
  }

  function move(dir) {
    if (won) return;
    const next = slide(level.grid, ball, DIRS[dir]);
    if (next[0] === ball[0] && next[1] === ball[1]) return;
    ball = next;
    moves++;
    if (ball[0] === level.goal[0] && ball[1] === level.goal[1]) won = true;
    draw();
  }

  const KEYS = {
    ArrowUp: 'up', ArrowDown: 'down', ArrowLeft: 'left', ArrowRight: 'right',
    w: 'up', s: 'down', a: 'left', d: 'right',
  };
  document.addEventListener('keydown', (e) => {
    const dir = KEYS[e.key];
    if (dir) { e.preventDefault(); move(dir); }
  });
  document.querySelectorAll('[data-dir]').forEach((b) =>
    b.addEventListener('click', () => move(b.dataset.dir)));
  document.getElementById('new').addEventListener('click', newLevel);

  newLevel();
}

// ------------------------------------------------------------------ tests ---

if (typeof document === 'undefined') {
  const assert = require('assert');

  // A ball with nothing in the way crosses the whole board.
  const open = Array.from({ length: SIZE }, () => Array(SIZE).fill(0));
  assert.deepStrictEqual(slide(open, [3, 3], DIRS.right), [3, SIZE - 1]);
  assert.deepStrictEqual(slide(open, [3, 3], DIRS.up), [0, 3]);

  // It stops one short of a wall, and a wall right next to it means no move.
  const walled = open.map((row) => row.slice());
  walled[3][6] = 1;
  assert.deepStrictEqual(slide(walled, [3, 3], DIRS.right), [3, 5]);
  assert.deepStrictEqual(slide(walled, [3, 5], DIRS.right), [3, 5]);

  // On an open board the ball can only ever rest on 9 cells: where it starts,
  // the four edge cells it first slides to, and the four corners.
  assert.strictEqual(reachable(open, [3, 3]).size, 9);

  // Every generated level is solvable, and par is the true distance.
  for (let i = 0; i < 200; i++) {
    const { grid, start, goal, par } = generate();
    const dist = reachable(grid, start);
    assert.strictEqual(dist.get(goal.join(',')), par);
    assert.ok(par >= 6);
    assert.strictEqual(grid[goal[0]][goal[1]], 0);
  }

  console.log('all tests passed');
}
