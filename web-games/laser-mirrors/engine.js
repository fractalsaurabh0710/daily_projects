'use strict';
// Beam physics, puzzle generation and solvability checking for Laser Mirrors.
// Shared by index.html (via <script src>) and by the self-test below (node engine.js).

var N = 7;
var DIRS = { R: [1, 0], L: [-1, 0], U: [0, -1], D: [0, 1] };

function key(x, y) { return x + ',' + y; }

// A '/' mirror maps (dx,dy) -> (-dy,-dx); a '\' mirror maps it to (dy,dx).
// (0 - v) rather than -v so a zero component never comes back as -0.
function reflect(d, m) { return m === '/' ? [0 - d[1], 0 - d[0]] : [d[1], d[0]]; }

function inGrid(x, y) { return x >= 0 && y >= 0 && x < N && y < N; }

// Fire the beam and report every cell it crosses plus where it leaves the grid.
// exit is the first out-of-bounds cell, or null if the beam is caught in a loop.
function trace(mirrors, entry) {
  var d = DIRS[entry.d], dx = d[0], dy = d[1];
  var x = entry.x, y = entry.y, path = [];
  for (var step = 0; step < N * N * 4; step++) {
    if (!inGrid(x, y)) return { path: path, exit: { x: x, y: y } };
    path.push([x, y]);
    var m = mirrors.get(key(x, y));
    if (m) { var r = reflect([dx, dy], m); dx = r[0]; dy = r[1]; }
    x += dx; y += dy;
  }
  return { path: path, exit: null };
}

function solved(mirrors, entry, target) {
  var e = trace(mirrors, entry).exit;
  return !!e && e.x === target.x && e.y === target.y;
}

// Lay out a puzzle by walking a beam and dropping mirrors as it goes, so the
// exit it happens to reach is a target that is reachable by construction.
// Then flip some mirrors: the walk's own layout is still a solution.
function generate(rand) {
  rand = rand || Math.random;
  for (var attempt = 0; attempt < 800; attempt++) {
    var entry = { x: 0, y: 1 + Math.floor(rand() * (N - 2)), d: 'R' };
    var sol = new Map(), dx = 1, dy = 0, x = entry.x, y = entry.y, placed = 0;
    for (var len = 0; len < 60 && inGrid(x, y); len++) {
      var k = key(x, y), m = sol.get(k);
      if (!m && placed < 6 && rand() < 0.5) {
        var opts = ['/', '\\'].filter(function (o) {
          var r = reflect([dx, dy], o);
          return inGrid(x + r[0], y + r[1]);
        });
        if (opts.length) { m = opts[Math.floor(rand() * opts.length)]; sol.set(k, m); placed++; }
      }
      if (m) { var r2 = reflect([dx, dy], m); dx = r2[0]; dy = r2[1]; }
      x += dx; y += dy;
    }
    if (placed < 4) continue;
    var end = trace(sol, entry).exit;
    if (!end) continue;
    for (var t = 0; t < 40; t++) {
      var start = new Map(), flips = 0;
      sol.forEach(function (v, k2) {
        var flip = rand() < 0.6;
        start.set(k2, flip ? (v === '/' ? '\\' : '/') : v);
        if (flip) flips++;
      });
      if (flips < 2 || solved(start, entry, end)) continue;
      return { entry: entry, target: end, mirrors: start, solution: sol };
    }
  }
  throw new Error('generator exhausted');
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = { N: N, DIRS: DIRS, key: key, reflect: reflect, trace: trace, solved: solved, generate: generate };
  if (require.main === module) {
    var assert = require('assert');
    // Physics: the four quadrant turns of each mirror.
    assert.deepStrictEqual(reflect(DIRS.R, '/'), DIRS.U);
    assert.deepStrictEqual(reflect(DIRS.D, '/'), DIRS.L);
    assert.deepStrictEqual(reflect(DIRS.R, '\\'), DIRS.D);
    assert.deepStrictEqual(reflect(DIRS.U, '\\'), DIRS.L);
    // Deterministic PRNG so a failure is reproducible.
    var seed = 12345;
    var rand = function () { seed = (seed * 1103515245 + 12345) % 2147483648; return seed / 2147483648; };
    var mirrorCounts = 0;
    for (var i = 0; i < 2000; i++) {
      var p = generate(rand);
      assert.ok(p.mirrors.size >= 4, 'at least 4 mirrors');
      assert.ok(solved(p.solution, p.entry, p.target), 'generated solution reaches the target');
      assert.ok(!solved(p.mirrors, p.entry, p.target), 'puzzle does not start solved');
      assert.strictEqual(p.mirrors.size, p.solution.size, 'scramble only flips, never moves');
      mirrorCounts += p.mirrors.size;
    }
    console.log('ok: 2000 puzzles, each solvable and none pre-solved');
    console.log('    mean mirrors per puzzle: ' + (mirrorCounts / 2000).toFixed(2));
  }
}
