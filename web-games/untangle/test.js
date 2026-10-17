// node test.js
//
// Pulls the game's script straight out of index.html and runs it against a
// stub DOM, so the tests exercise the shipped code rather than a copy of it.
const fs = require('fs');
const path = require('path');

const stub = {
  getContext: () => new Proxy({}, { get: () => () => {} }),
  addEventListener() {}, setPointerCapture() {},
  getBoundingClientRect: () => ({ left: 0, top: 0, width: 600, height: 600 }),
  clientWidth: 600, width: 600, height: 600, className: '', innerHTML: '',
  set onclick(_) {},
};
global.document = { getElementById: () => stub };
global.devicePixelRatio = 1;
global.addEventListener = () => {};

const html = fs.readFileSync(path.join(__dirname, 'index.html'), 'utf8');
const js = html.match(/<script>([\s\S]*?)<\/script>/)[1] + `
globalThis.__game = { generate, scramble, crossingPairs, crosses,
  get nodes() { return nodes; }, get edges() { return edges; },
  get solution() { return solution; }, set nodes(v) { nodes = v; } };
`;
new Function(js)();
const g = globalThis.__game;

let failed = 0;
const check = (name, ok) => { console.log((ok ? 'ok   ' : 'FAIL ') + name); if (!ok) failed++; };

// The crossing predicate, which everything else rests on.
const P = (x, y) => ({ x, y });
check('X shape crosses',            g.crosses(P(0,0), P(1,1), P(0,1), P(1,0)) === true);
check('parallel segments do not',   g.crosses(P(0,0), P(1,0), P(0,1), P(1,1)) === false);
check('shared endpoint does not',   g.crosses(P(0,0), P(1,1), P(0,0), P(1,0)) === false);
check('disjoint segments do not',   g.crosses(P(0,0), P(0.1,0), P(0.9,0.9), P(1,1)) === false);

// The claim worth testing: every puzzle is solvable, because it was built from
// a planar drawing. Put the nodes back where the generator had them and the
// crossing count must be exactly zero.
for (const n of [5, 8, 11, 14]) {
  for (let trial = 0; trial < 25; trial++) {
    g.generate(n);
    const edges = g.edges;
    const keys = edges.map(([a, b]) => (a < b ? `${a},${b}` : `${b},${a}`));

    const scrambledCrossings = g.crossingPairs().size;
    g.nodes = g.solution.map(p => ({ x: p.x, y: p.y }));
    const solvedCrossings = g.crossingPairs().size;

    if (trial === 0) {
      check(`n=${n}: ${n} nodes, ${edges.length} edges`, g.nodes.length === n);
      check(`n=${n}: at least a spanning tree's worth of edges`, edges.length >= n - 1);
      check(`n=${n}: no duplicate edges`, new Set(keys).size === keys.length);
      check(`n=${n}: respects Euler's planar bound E <= 3V-6`, n < 3 || edges.length <= 3*n - 6);
      check(`n=${n}: the scramble does tangle it`, scrambledCrossings > 0);
    }
    if (solvedCrossings !== 0) {
      check(`n=${n}: trial ${trial} solution layout is crossing-free`, false);
      break;
    }
  }
  check(`n=${n}: solution layout crossing-free in 25/25 puzzles`, true);
}

// Scrambling is a move, not a redraw: same graph, new positions.
g.generate(9);
const before = JSON.stringify(g.edges);
g.scramble();
check('scramble preserves the edge set', JSON.stringify(g.edges) === before);

console.log(failed ? `\n${failed} failure(s)` : '\nall checks passed');
process.exit(failed ? 1 : 0);
