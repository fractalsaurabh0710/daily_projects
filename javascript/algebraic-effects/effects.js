// Algebraic effects in ~80 lines of generators.
//
// A generator that `yield perform(...)` says WHAT it wants, never HOW. A handler
// stack decides the how. Unlike try/catch, a handler returns a value *back into*
// the generator, which resumes where it left off -- so "failure" can be recovered
// from at the failure point rather than unwound to.

class Effect {
  constructor(type, payload) { this.type = type; this.payload = payload; }
}

/** Inside a generator: `const x = yield perform('fetchUser', id)`. */
const perform = (type, payload) => new Effect(type, payload);

class Unhandled extends Error {
  constructor(effect) {
    super(`unhandled effect: ${effect.type}`);
    this.name = 'Unhandled';
    this.effect = effect;
  }
}

const isGen = (v) => v && typeof v.next === 'function' && typeof v.throw === 'function';
const isPromise = (v) => v && typeof v.then === 'function';

/**
 * handle(handlers, genFn) -> a generator function with those effects interpreted.
 *
 * Returning a generator function (rather than running anything) is what makes
 * handlers compose: an effect this layer does not know is re-yielded outward to
 * whoever wraps it, and a handler may itself `perform` effects belonging to an
 * outer layer. Nothing here knows whether the program ends up sync or async.
 */
function handle(handlers, genFn) {
  return function* (...args) {
    const it = genFn(...args);
    let resume = { throw: false, value: undefined };
    for (;;) {
      const step = resume.throw ? it.throw(resume.value) : it.next(resume.value);
      if (step.done) return step.value;

      const eff = step.value;
      const h = eff instanceof Effect ? handlers[eff.type] : undefined;

      if (!h) {
        // Not ours. Pass it outward verbatim, and pass the answer back in.
        try { resume = { throw: false, value: yield eff }; }
        catch (err) { resume = { throw: true, value: err }; }
        continue;
      }

      try {
        let r = h(eff.payload);
        if (isGen(r)) r = yield* r;        // handler performs effects of its own
        if (isPromise(r)) r = yield r;     // handler is async: bubble to the runner
        resume = { throw: false, value: r };
      } catch (err) {
        resume = { throw: true, value: err };
      }
    }
  };
}

/** Drive a handled generator, awaiting any promise a handler bubbled up. */
async function run(genFn, ...args) {
  const it = genFn(...args);
  let resume = { throw: false, value: undefined };
  for (;;) {
    const step = resume.throw ? it.throw(resume.value) : it.next(resume.value);
    if (step.done) return step.value;
    if (step.value instanceof Effect) throw new Unhandled(step.value);
    try { resume = { throw: false, value: await step.value }; }
    catch (err) { resume = { throw: true, value: err }; }
  }
}

/** Same, but refuses to await: proves a program's handlers are all synchronous. */
function runSync(genFn, ...args) {
  const it = genFn(...args);
  let resume;
  for (;;) {
    const step = resume ? it.next(resume) : it.next();
    if (step.done) return step.value;
    if (step.value instanceof Effect) throw new Unhandled(step.value);
    throw new Error('runSync: a handler returned a promise');
  }
}

// ---------------------------------------------------------------- demo + tests

const assert = require('node:assert/strict');

// Business logic. No database, no clock, no logger -- and no async either.
function* loadReport(ids) {
  const lines = [];
  for (const id of ids) {
    const user = yield perform('fetchUser', id);
    if (!user) { yield perform('log', `skipped ${id}`); continue; }
    lines.push(`${user.name} <${user.email}>`);
  }
  yield perform('log', `${lines.length} of ${ids.length} resolved`);
  return lines;
}

const USERS = {
  1: { name: 'Ada', email: 'ada@example.com' },
  3: { name: 'Grace', email: 'grace@example.com' },
};
const EXPECTED = ['Ada <ada@example.com>', 'Grace <grace@example.com>'];
const EXPECTED_LOG = ['skipped 2', '2 of 3 resolved'];

async function main() {
  // 1. Synchronous interpretation: a plain table, no I/O at all.
  let log = [];
  const sync = handle({ fetchUser: (id) => USERS[id], log: (m) => void log.push(m) }, loadReport);
  assert.deepEqual(runSync(sync, [1, 2, 3]), EXPECTED);
  assert.deepEqual(log, EXPECTED_LOG);

  // 2. Asynchronous interpretation of the *same* generator, untouched.
  log = [];
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const async_ = handle({
    fetchUser: async (id) => { await sleep(1); return USERS[id]; },
    log: (m) => void log.push(m),
  }, loadReport);
  assert.deepEqual(await run(async_, [1, 2, 3]), EXPECTED);
  assert.deepEqual(log, EXPECTED_LOG);

  // 3. Nested layers: the inner `log` handler performs `now`, which only the
  //    outer layer knows about. The effect travels outward and the timestamp
  //    travels back in.
  const stamped = [];
  const inner = handle({
    fetchUser: (id) => USERS[id],
    log: function* (m) { stamped.push(`[${yield perform('now')}] ${m}`); },
  }, loadReport);
  const outer = handle({ now: () => 'T0' }, inner);
  assert.deepEqual(runSync(outer, [1, 2, 3]), EXPECTED);
  assert.deepEqual(stamped, ['[T0] skipped 2', '[T0] 2 of 3 resolved']);

  // 4. Recovery that try/catch around the caller cannot express. The inner
  //    layer re-performs `fetchUser` outward; when the outer, flaky one raises,
  //    the throw lands at that `yield` and the handler returns a placeholder --
  //    so `loadReport` resumes mid-loop with a value instead of unwinding.
  const flaky = handle({
    fetchUser: (id) => { if (id === 3) throw new Error('timeout'); return USERS[id]; },
    log: () => {},
  }, handle({
    fetchUser: function* (id) {
      try { return yield perform('fetchUser', id); }
      catch { return { name: 'unknown', email: `id-${id}` }; }
    },
  }, loadReport));
  assert.deepEqual(runSync(flaky, [1, 3]), ['Ada <ada@example.com>', 'unknown <id-3>']);

  // 5. An effect nobody handles is a named error, not a silent hang.
  assert.throws(() => runSync(handle({}, loadReport), [1]), Unhandled);

  console.log('all 5 checks passed');
  console.log('sync and async runs produced identical output:', EXPECTED.join(', '));
}

if (require.main === module) main();
module.exports = { perform, handle, run, runSync, Effect, Unhandled };
