// Reactive signals in ~120 lines: automatic dependency tracking, no dependency
// declarations, no virtual DOM, no libraries. The same core idea behind Solid,
// Vue's reactivity, and Preact signals.
//
// The trick is a module-level "who is listening right now" stack. Reading a
// signal inside a computation registers the edge; re-running a computation
// first tears down its old edges, so dependencies are discovered fresh every
// run and conditional branches cannot leave stale subscriptions behind.

let ACTIVE = null;        // the computation currently executing, if any
const STACK = [];         // nesting of computations
let BATCH = null;         // pending set of computations during batch()

function link(dep, sub) {
  dep.subs.add(sub);
  sub.deps.add(dep);
}

function unlinkAll(sub) {
  for (const dep of sub.deps) dep.subs.delete(sub);
  sub.deps.clear();
}

function notify(dep) {
  // Copy: a subscriber may re-link during its own run.
  for (const sub of [...dep.subs]) {
    if (BATCH) BATCH.add(sub);
    else sub.run();
  }
}

/** A writable reactive value. Returns [read, write]. */
export function signal(initial, { equals = Object.is } = {}) {
  const node = { value: initial, subs: new Set() };

  const read = () => {
    if (ACTIVE) link(node, ACTIVE);
    return node.value;
  };

  const write = (next) => {
    const value = typeof next === 'function' ? next(node.value) : next;
    if (equals(value, node.value)) return node.value;  // no-op writes are free
    node.value = value;
    notify(node);
    return value;
  };

  return [read, write];
}

function computation(fn, { lazy }) {
  const node = { deps: new Set(), subs: new Set(), stale: true, value: undefined };

  node.run = () => {
    if (lazy) {
      // A computed does not recompute eagerly; it marks itself dirty and
      // propagates staleness so downstream effects know to re-read.
      node.stale = true;
      notify(node);
      return;
    }
    recompute();
  };

  function recompute() {
    unlinkAll(node);
    STACK.push(ACTIVE);
    ACTIVE = node;
    try {
      node.value = fn(node.value);
      node.stale = false;
    } finally {
      ACTIVE = STACK.pop();
    }
    return node.value;
  }

  node.recompute = recompute;
  return node;
}

/** A derived value. Recomputes only when read after one of its inputs changed. */
export function computed(fn) {
  const node = computation(fn, { lazy: true });
  return () => {
    if (node.stale) node.recompute();
    if (ACTIVE) link(node, ACTIVE);
    return node.value;
  };
}

/** Run fn now, and again whenever anything it read changes. Returns a disposer. */
export function effect(fn) {
  const node = computation(fn, { lazy: false });
  node.run();
  return () => unlinkAll(node);
}

/** Collapse many writes into one round of effect runs. */
export function batch(fn) {
  if (BATCH) return fn();          // already batching; join the outer one
  BATCH = new Set();
  try {
    return fn();
  } finally {
    const pending = BATCH;
    BATCH = null;
    for (const sub of pending) sub.run();
  }
}

/** Read without subscribing. */
export function untrack(fn) {
  STACK.push(ACTIVE);
  ACTIVE = null;
  try {
    return fn();
  } finally {
    ACTIVE = STACK.pop();
  }
}
