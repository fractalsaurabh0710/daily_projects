'use strict';
// Is `arr.sort(() => Math.random() - 0.5)` a shuffle?  It is not, and the shape
// of the bias is a fingerprint of the engine's sort algorithm.  Everything below
// is measured, not asserted: the position matrix M[v][p] counts how often value
// v lands at position p, and a uniform shuffle makes every cell trials/n.

// Seeded PRNG so every number printed here is reproducible.
function mulberry32(seed) {
  let a = seed >>> 0;
  return function () {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function fisherYates(arr, rnd) {
  const a = arr.slice();
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

// The idiom under test.  The comparator is not a consistent ordering, so the
// sort's output depends entirely on which comparisons it happens to make.
function comparatorShuffle(arr, rnd) {
  return arr.slice().sort(() => rnd() - 0.5);
}

function positionMatrix(n, trials, shuffle, rnd) {
  const ident = Array.from({ length: n }, (_, i) => i);
  const M = Array.from({ length: n }, () => new Array(n).fill(0));
  for (let t = 0; t < trials; t++) {
    const out = shuffle(ident, rnd);
    for (let p = 0; p < n; p++) M[out[p]][p]++;
  }
  return M;
}

// Each row and each column of M sums to `trials`, which pins (n-1)^2 free cells.
function chiSquare(M, trials) {
  const n = M.length;
  const e = trials / n;
  let x2 = 0;
  for (const row of M) for (const o of row) x2 += ((o - e) * (o - e)) / e;
  return { x2, dof: (n - 1) * (n - 1), ratio: x2 / ((n - 1) * (n - 1)) };
}

function maxBias(M, trials) {
  const e = trials / M.length;
  let worst = 0;
  for (const row of M) for (const o of row) worst = Math.max(worst, Math.abs(o - e) / e);
  return worst;
}

// How much the main diagonal -- value v still sitting at position v -- is
// enriched over the uniform expectation.  1.0 means no memory of the input.
function diagonalEnrichment(M, trials) {
  const n = M.length;
  const e = trials / n;
  let sum = 0;
  for (let v = 0; v < n; v++) sum += M[v][v] / e;
  return sum / n;
}

function printMatrix(label, M, trials) {
  const n = M.length;
  const e = trials / n;
  console.log(`\n${label}  (cells as % of the uniform expectation, 100 = unbiased)`);
  console.log('        ' + Array.from({ length: n }, (_, p) => `p${p}`.padStart(6)).join(''));
  for (let v = 0; v < n; v++) {
    const cells = M[v].map((o) => ((o / e) * 100).toFixed(0).padStart(6)).join('');
    console.log(`  v${v}  ${cells}`);
  }
}

const N = 6;
const TRIALS = 200000;
const rnd = mulberry32(12345);

const fy = positionMatrix(N, TRIALS, fisherYates, rnd);
const cs = positionMatrix(N, TRIALS, comparatorShuffle, rnd);

printMatrix(`Fisher-Yates, n=${N}, ${TRIALS} trials`, fy, TRIALS);
printMatrix(`sort(() => rnd() - 0.5), n=${N}, ${TRIALS} trials`, cs, TRIALS);

const fyChi = chiSquare(fy, TRIALS);
const csChi = chiSquare(cs, TRIALS);
console.log(`\n  Fisher-Yates : chi2/dof = ${fyChi.ratio.toFixed(2)}  max cell bias ${(maxBias(fy, TRIALS) * 100).toFixed(1)}%  diagonal x${diagonalEnrichment(fy, TRIALS).toFixed(2)}`);
console.log(`  comparator   : chi2/dof = ${csChi.ratio.toFixed(2)}  max cell bias ${(maxBias(cs, TRIALS) * 100).toFixed(1)}%  diagonal x${diagonalEnrichment(cs, TRIALS).toFixed(2)}`);
console.log(`  (chi2/dof near 1 is what uniformity looks like; ${csChi.ratio.toFixed(0)} is not noise)`);

// The bias is a property of the sort, so it changes when the engine changes
// strategy with array length.  V8's TimSort runs short arrays as a single
// binary-insertion run and only starts merging above a threshold.
console.log('\n  How the bias scales with n (20000 trials each):');
console.log('      n   chi2/dof   max cell bias   diagonal enrichment   comparisons/element');
for (const n of [2, 4, 8, 16, 32, 48, 64, 96, 128]) {
  const T = 20000;
  const M = positionMatrix(n, T, comparatorShuffle, rnd);
  // Count the comparisons the engine actually asks for, per element.
  let calls = 0;
  Array.from({ length: n }, (_, i) => i).sort(() => {
    calls++;
    return rnd() - 0.5;
  });
  console.log(
    `  ${String(n).padStart(5)}   ${chiSquare(M, T).ratio.toFixed(1).padStart(8)}   ` +
      `${(maxBias(M, T) * 100).toFixed(0).padStart(12)}%   ` +
      `${('x' + diagonalEnrichment(M, T).toFixed(2)).padStart(19)}   ${(calls / n).toFixed(1).padStart(19)}`
  );
}

// Claims demonstrated rather than stated.
const assert = require('assert');
assert.ok(fyChi.ratio < 2, 'Fisher-Yates should look uniform');
assert.ok(maxBias(fy, TRIALS) < 0.05, 'Fisher-Yates cells should sit near expectation');
assert.ok(csChi.ratio > 10, 'comparator sort should be detectably non-uniform');
assert.ok(diagonalEnrichment(cs, TRIALS) > 1.2, 'comparator sort should leave values near where they started');
assert.ok(Math.abs(diagonalEnrichment(fy, TRIALS) - 1) < 0.02, 'Fisher-Yates should have no diagonal memory');
console.log('\n  all assertions passed');
