'use strict';
// Minesweeper board generator that only emits boards solvable by pure logic,
// plus the constraint solver used to prove it. Shared by index.html and the
// self-test at the bottom (`node solver.js`).

const UNKNOWN = 0, SAFE = 1, MINE = 2;

function neighbors(i, W, H) {
  const x = i % W, y = (i - x) / W, out = [];
  for (let dy = -1; dy <= 1; dy++) {
    for (let dx = -1; dx <= 1; dx++) {
      if (!dx && !dy) continue;
      const nx = x + dx, ny = y + dy;
      if (nx >= 0 && nx < W && ny >= 0 && ny < H) out.push(ny * W + nx);
    }
  }
  return out;
}

function counts(mine, W, H) {
  const c = new Uint8Array(W * H);
  for (let i = 0; i < W * H; i++) {
    if (mine[i]) continue;
    for (const j of neighbors(i, W, H)) if (mine[j]) c[i]++;
  }
  return c;
}

// Play the board the way a perfect logician would: open the start cell, then
// apply two rules until nothing new follows. Rule 1 is the obvious one, read off
// a single number. Rule 2 compares two numbers whose unknown neighbours nest:
// if A's cells are a subset of B's, then B's extra cells hold exactly
// B.n - A.n mines, which is decisive when that is 0 or all of them.
function solve(mine, W, H, start) {
  const N = W * H, cnt = counts(mine, W, H), known = new Uint8Array(N);

  const open = (i) => {
    const st = [i];
    while (st.length) {
      const k = st.pop();
      if (known[k] === SAFE) continue;
      known[k] = SAFE;
      if (cnt[k] === 0) for (const j of neighbors(k, W, H)) if (!known[j]) st.push(j);
    }
  };
  open(start);

  let progress = true, rounds = 0;
  while (progress) {
    progress = false;
    rounds++;
    const cs = [];
    for (let i = 0; i < N; i++) {
      if (known[i] !== SAFE || cnt[i] === 0) continue;
      const un = [];
      let m = 0;
      for (const j of neighbors(i, W, H)) {
        if (known[j] === MINE) m++;
        else if (known[j] === UNKNOWN) un.push(j);
      }
      if (un.length) cs.push({ cells: un, n: cnt[i] - m });
    }

    const safe = new Set(), mines = new Set();
    const mark = (c) => {
      if (!c.cells.length) return;
      if (c.n === 0) for (const x of c.cells) safe.add(x);
      else if (c.n === c.cells.length) for (const x of c.cells) mines.add(x);
    };
    for (const c of cs) mark(c);

    if (!safe.size && !mines.size) {            // rule 1 exhausted, try rule 2
      for (const a of cs) {
        const as = new Set(a.cells);
        for (const b of cs) {
          if (a === b || a.cells.length >= b.cells.length) continue;
          const bs = new Set(b.cells);
          if (!a.cells.every((x) => bs.has(x))) continue;
          mark({ cells: b.cells.filter((x) => !as.has(x)), n: b.n - a.n });
        }
      }
    }

    for (const i of mines) if (!known[i]) { known[i] = MINE; progress = true; }
    for (const i of safe) if (!known[i]) { open(i); progress = true; }
  }

  let unknown = 0;
  for (let i = 0; i < N; i++) if (!known[i]) unknown++;
  return { solved: unknown === 0, unknown, rounds };
}

function mulberry32(seed) {
  return function () {
    seed = (seed + 0x6D2B79F5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

// A random board plus a start cell whose 3x3 neighbourhood is mine-free, which
// is what every implementation guarantees for the first click.
function randomBoard(W, H, M, rand) {
  const N = W * H, start = Math.floor(rand() * N);
  const banned = new Set([start, ...neighbors(start, W, H)]);
  const pool = [];
  for (let i = 0; i < N; i++) if (!banned.has(i)) pool.push(i);
  for (let k = 0; k < M; k++) {
    const j = k + Math.floor(rand() * (pool.length - k));
    [pool[k], pool[j]] = [pool[j], pool[k]];
  }
  const mine = new Uint8Array(N);
  for (let k = 0; k < M; k++) mine[pool[k]] = 1;
  return { mine, start };
}

function generate(W, H, M, rand = Math.random, maxTries = 20000) {
  for (let t = 1; t <= maxTries; t++) {
    const b = randomBoard(W, H, M, rand);
    if (solve(b.mine, W, H, b.start).solved) return { ...b, attempts: t };
  }
  return null;
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { neighbors, counts, solve, generate, randomBoard, mulberry32 };
}

if (typeof require !== 'undefined' && require.main === module) {
  const W = 9, H = 9, M = 10, T = 400;
  const rand = mulberry32(20261113);

  let guessy = 0, leftover = 0;
  for (let k = 0; k < T; k++) {
    const b = randomBoard(W, H, M, rand);
    const r = solve(b.mine, W, H, b.start);
    if (!r.solved) { guessy++; leftover += r.unknown; }
  }

  let attempts = 0, worst = 0, rounds = 0;
  for (let k = 0; k < T; k++) {
    const g = generate(W, H, M, rand);
    if (!g) throw new Error('no logic-solvable board found');
    const r = solve(g.mine, W, H, g.start);
    if (!r.solved) throw new Error('generator emitted a board needing a guess');
    attempts += g.attempts;
    worst = Math.max(worst, g.attempts);
    rounds += r.rounds;
  }

  console.log(`${W}x${H}, ${M} mines, ${T} boards each way`);
  console.log(`raw random boards needing a guess: ${guessy}/${T} ` +
    `(${(100 * guessy / T).toFixed(1)}%), ${(leftover / Math.max(1, guessy)).toFixed(1)} cells left undecided on average`);
  console.log(`filtered boards: ${T}/${T} solvable by logic, ` +
    `${(attempts / T).toFixed(1)} candidates tried per board (worst ${worst}), ` +
    `${(rounds / T).toFixed(1)} deduction rounds to finish`);
  console.log('ok');
}
