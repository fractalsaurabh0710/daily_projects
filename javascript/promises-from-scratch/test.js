'use strict';
const assert = require('assert');
const TinyPromise = require('./promise');

// The same program, written once, run against whatever constructor it is given.
// If TinyPromise schedules on the same microtask ticks as the native Promise,
// both runs produce byte-identical logs — not just the same set of lines, the
// same *interleaving*.
function program(P, log) {
  log('sync start');

  P.resolve('a').then((v) => log(`1 ${v}`)).then(() => log('2 after a'));

  const inner = P.resolve('inner');
  P.resolve('b')
    .then(() => { log('1 b'); return inner; })   // returning a thenable: +2 ticks
    .then((v) => log(`2 adopted ${v}`))
    .then(() => log('3 after adopt'));

  new P((res) => { log('executor runs sync'); res('c'); })
    .then((v) => log(`1 ${v}`))
    .then(() => log('2 after c'));

  P.reject(new Error('boom'))
    .then(() => log('never'))                    // no handler: pass-through, +1 tick
    .catch((e) => log(`3 caught ${e.message}`))
    .then(() => log('4 after catch'));

  P.all([P.resolve(1), 2, P.resolve(3)]).then((v) => log(`all ${v.join(',')}`));

  log('sync end');
}

function run(P) {
  const logs = [];
  program(P, (line) => logs.push(line));
  // Timers fire only once the microtask queue is empty, so this captures
  // everything the program will ever log.
  return new Promise((done) => setTimeout(() => done(logs), 0));
}

async function main() {
  const native = await run(Promise);
  const tiny = await run(TinyPromise);

  console.log('native            | tiny');
  console.log('------------------+------------------');
  const width = Math.max(...native.map((s) => s.length), 18);
  for (let i = 0; i < Math.max(native.length, tiny.length); i++) {
    const a = native[i] ?? '—', b = tiny[i] ?? '—';
    console.log(`${a.padEnd(width)} | ${b}${a === b ? '' : '   <-- MISMATCH'}`);
  }
  assert.deepStrictEqual(tiny, native, 'tick-for-tick ordering must match native');
  console.log('\nordering: identical to native, line for line');

  // Spec corners worth pinning down.
  const cyclic = TinyPromise.resolve().then(function () { return p; });
  const p = cyclic;
  await new Promise((r) => setTimeout(r, 0));
  assert.strictEqual(cyclic.state, 'rejected');
  assert.ok(cyclic.value instanceof TypeError, 'returning the same promise is a TypeError');

  const multi = new TinyPromise((res, rej) => { res('first'); res('second'); rej(new Error('late')); });
  await new Promise((r) => setTimeout(r, 0));
  assert.strictEqual(multi.value, 'first', 'resolve is a one-shot');

  const foreign = { then(res) { res('from a plain object'); } };
  assert.strictEqual(await TinyPromise.resolve(foreign), 'from a plain object');

  assert.deepStrictEqual(await TinyPromise.all([]), []);
  assert.strictEqual(await TinyPromise.race([new TinyPromise(() => {}), TinyPromise.resolve('fast')]), 'fast');

  let ran = false;
  await TinyPromise.reject(new Error('e')).finally(() => { ran = true; }).catch(() => {});
  assert.ok(ran, 'finally runs on the rejected path too');

  console.log('spec corners: all pass');
}

main().catch((e) => { console.error(e.message); process.exit(1); });
