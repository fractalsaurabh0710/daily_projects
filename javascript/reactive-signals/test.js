import assert from 'node:assert/strict';
import { signal, computed, effect, batch, untrack } from './signals.js';

const tests = [];
const test = (name, fn) => tests.push([name, fn]);

test('effect runs once up front and again on write', () => {
  const [count, setCount] = signal(0);
  const seen = [];
  effect(() => seen.push(count()));
  setCount(1);
  setCount(2);
  assert.deepEqual(seen, [0, 1, 2]);
});

test('a write with an equal value wakes nobody', () => {
  const [name, setName] = signal('ada');
  let runs = 0;
  effect(() => { name(); runs++; });
  setName('ada');
  assert.equal(runs, 1);
});

test('computed derives, and is lazy until read', () => {
  const [n, setN] = signal(2);
  let evaluations = 0;
  const squared = computed(() => { evaluations++; return n() * n(); });
  assert.equal(evaluations, 0, 'not evaluated before first read');
  assert.equal(squared(), 4);
  assert.equal(squared(), 4);
  assert.equal(evaluations, 1, 'cached between reads');
  setN(5);
  assert.equal(squared(), 25);
  assert.equal(evaluations, 2);
});

test('computeds chain', () => {
  const [base, setBase] = signal(1);
  const doubled = computed(() => base() * 2);
  const plusTen = computed(() => doubled() + 10);
  assert.equal(plusTen(), 12);
  setBase(4);
  assert.equal(plusTen(), 18);
});

test('dependencies are rediscovered, so dead branches stop firing', () => {
  const [useA, setUseA] = signal(true);
  const [a, setA] = signal('a');
  const [b, setB] = signal('b');
  const seen = [];
  effect(() => seen.push(useA() ? a() : b()));
  setB('b2');                 // b is not read on this branch: ignored
  assert.deepEqual(seen, ['a']);
  setUseA(false);             // now b is live and a is not
  setA('a2');
  assert.deepEqual(seen, ['a', 'b2']);
});

test('batch collapses writes into one effect run', () => {
  const [x, setX] = signal(0);
  const [y, setY] = signal(0);
  let runs = 0;
  effect(() => { x(); y(); runs++; });
  assert.equal(runs, 1);
  batch(() => { setX(1); setY(1); setX(2); });
  assert.equal(runs, 2, 'three writes, one re-run');
});

test('untrack reads without subscribing', () => {
  const [tracked, setTracked] = signal(0);
  const [quiet, setQuiet] = signal(0);
  let runs = 0;
  effect(() => { tracked(); untrack(quiet); runs++; });
  setQuiet(99);
  assert.equal(runs, 1);
  setTracked(1);
  assert.equal(runs, 2);
});

test('disposing an effect detaches it', () => {
  const [v, setV] = signal(0);
  let runs = 0;
  const dispose = effect(() => { v(); runs++; });
  setV(1);
  dispose();
  setV(2);
  assert.equal(runs, 2);
});

test('an effect reading a computed re-runs when the root changes', () => {
  const [price, setPrice] = signal(10);
  const [qty, setQty] = signal(2);
  const total = computed(() => price() * qty());
  const seen = [];
  effect(() => seen.push(total()));
  setQty(3);
  batch(() => { setPrice(1); setQty(1); });
  assert.deepEqual(seen, [20, 30, 1]);
});

let failed = 0;
for (const [name, fn] of tests) {
  try {
    fn();
    console.log(`  ok   ${name}`);
  } catch (err) {
    failed++;
    console.log(`  FAIL ${name}\n       ${err.message.split('\n')[0]}`);
  }
}
console.log(`\n${tests.length - failed}/${tests.length} passing`);
process.exit(failed ? 1 : 0);
