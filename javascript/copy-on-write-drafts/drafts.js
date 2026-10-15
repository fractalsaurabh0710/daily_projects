'use strict';
// Copy-on-write drafts: mutate a plain object freely, get back an immutable
// copy that shares every subtree you did not touch. ~130 lines, no deps.
//
// The trick is that a draft is a Proxy that reads through to the original and
// only allocates a shallow copy at the moment it is written to -- and when it
// does, it tells its parent to copy too, so the path from the root to the
// change is fresh and everything hanging off it is still the original object.

const INTERNAL = Symbol('draftState');

function isDraftable(v) {
  return v !== null && typeof v === 'object' &&
    (Array.isArray(v) || Object.getPrototypeOf(v) === Object.prototype);
}

const shallowCopy = (v) => (Array.isArray(v) ? v.slice() : Object.assign({}, v));

// What reads see: the copy once it exists, otherwise the untouched original.
const source = (state) => state.copy || state.base;

function markChanged(state) {
  if (state.modified) return;
  state.modified = true;
  state.copy = shallowCopy(state.base);
  if (state.parent) markChanged(state.parent); // copy the spine, not the leaves
}

function createDraft(base, parent) {
  const state = { base, copy: null, parent, modified: false, children: new Map() };
  // The proxy target is a fresh empty object of the right shape, never `base`
  // itself: the traps answer from `source(state)` so the original is never
  // written to, and an empty target keeps the proxy invariants easy to satisfy.
  const target = Array.isArray(base) ? [] : {};
  const isArray = Array.isArray(base);

  state.proxy = new Proxy(target, {
    get(_t, prop) {
      if (prop === INTERNAL) return state;
      const value = source(state)[prop];
      if (!isDraftable(value)) return value;
      // Draft children lazily, and hand back the same draft on re-read so
      // `d.a.b = 1; d.a.c = 2` lands in one copy of `a`.
      const cached = state.children.get(prop);
      if (cached && cached[INTERNAL].base === value) return cached;
      const child = createDraft(value, state);
      state.children.set(prop, child);
      return child;
    },
    set(_t, prop, value) {
      const src = source(state);
      if (src[prop] === value && prop in src) return true; // writing the same value is not a change
      markChanged(state);
      state.children.delete(prop);
      state.copy[prop] = value && value[INTERNAL] ? finalize(value[INTERNAL]) : value;
      return true;
    },
    deleteProperty(_t, prop) {
      if (!(prop in source(state))) return true;
      markChanged(state);
      state.children.delete(prop);
      delete state.copy[prop];
      return true;
    },
    has: (_t, prop) => prop in source(state),
    ownKeys: () => Reflect.ownKeys(source(state)),
    getOwnPropertyDescriptor(_t, prop) {
      const d = Reflect.getOwnPropertyDescriptor(source(state), prop);
      if (!d) return undefined;
      // `length` on an array target is non-configurable, and a proxy may not
      // claim otherwise; everything else is reported plain and configurable.
      return {
        value: d.value,
        writable: true,
        enumerable: d.enumerable,
        configurable: !(isArray && prop === 'length'),
      };
    },
    getPrototypeOf: () => Object.getPrototypeOf(base),
  });
  return state.proxy;
}

function finalize(state) {
  if (!state.modified) return state.base; // untouched: hand back the original
  const out = state.copy;
  for (const [prop, child] of state.children) {
    const cs = child[INTERNAL];
    if (cs.modified) out[prop] = finalize(cs);
  }
  return out;
}

function produce(base, recipe) {
  if (!isDraftable(base)) throw new TypeError('produce() needs a plain object or array');
  const draft = createDraft(base, null);
  const result = recipe(draft);
  if (result !== undefined && result !== draft) return result; // recipe replaced the whole value
  return finalize(draft[INTERNAL]);
}

module.exports = { produce };

// ---------------------------------------------------------------- tests
if (require.main === module) {
  const assert = require('assert');
  const base = Object.freeze({
    user: { name: 'ada', tags: ['math', 'engines'] },
    settings: { theme: 'dark', nested: { deep: true } },
    counts: [1, 2, 3],
  });

  // A write produces a new root and a new spine, and shares the rest.
  let next = produce(base, (d) => { d.user.name = 'grace'; });
  assert.strictEqual(next.user.name, 'grace');
  assert.strictEqual(base.user.name, 'ada', 'base must not be touched');
  assert.notStrictEqual(next.user, base.user, 'changed subtree is copied');
  assert.strictEqual(next.settings, base.settings, 'untouched subtree is shared');
  assert.strictEqual(next.user.tags, base.user.tags, 'untouched sibling is shared');

  // Repeated writes inside one subtree copy it once.
  next = produce(base, (d) => { d.user.name = 'grace'; d.user.role = 'rear admiral'; });
  assert.deepStrictEqual(next.user, { name: 'grace', tags: base.user.tags, role: 'rear admiral' });

  // Arrays: mutating methods work through the traps.
  next = produce(base, (d) => { d.counts.push(4); d.counts[0] = 99; });
  assert.deepStrictEqual(next.counts, [99, 2, 3, 4]);
  assert.deepStrictEqual(base.counts, [1, 2, 3]);
  assert.ok(Array.isArray(next.counts) && next.counts.length === 4);

  // Deleting, and reading through to depth.
  next = produce(base, (d) => { delete d.settings.theme; d.settings.nested.deep = false; });
  assert.deepStrictEqual(next.settings, { nested: { deep: false } });
  assert.strictEqual(base.settings.nested.deep, true);
  assert.strictEqual(next.user, base.user);

  // A no-op recipe -- including writing back the identical value -- returns the
  // very same object, so a `prev === next` check upstream stays meaningful.
  assert.strictEqual(produce(base, () => {}), base);
  assert.strictEqual(produce(base, (d) => { d.user.name = 'ada'; }), base);
  assert.strictEqual(produce(base, (d) => { void d.user.tags[1]; }), base);

  // Drafts behave like the thing they stand in for while the recipe runs.
  produce(base, (d) => {
    assert.deepStrictEqual(Object.keys(d), ['user', 'settings', 'counts']);
    assert.ok('theme' in d.settings);
    assert.strictEqual(JSON.stringify(d), JSON.stringify(base));
    assert.deepStrictEqual(d.counts.map((n) => n * 2), [2, 4, 6]);
  });

  // Moving a draft into another slot finalizes it rather than leaking a proxy.
  next = produce(base, (d) => { d.user.tags.push('cobol'); d.moved = d.user; });
  assert.deepStrictEqual(next.moved.tags, ['math', 'engines', 'cobol']);
  assert.strictEqual(JSON.parse(JSON.stringify(next)).moved.name, 'ada');

  // The recipe may return a replacement outright.
  assert.deepStrictEqual(produce(base, () => ({ replaced: true })), { replaced: true });

  console.log('all tests passed');
}
