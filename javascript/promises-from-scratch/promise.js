'use strict';
// A Promise implementation built from queueMicrotask and nothing else.
// The goal is not "a thing that calls callbacks eventually" — it is to land on
// the *same microtask tick* as the native one for every callback. See test().

const PENDING = 'pending', FULFILLED = 'fulfilled', REJECTED = 'rejected';

class TinyPromise {
  constructor(executor) {
    if (typeof executor !== 'function') throw new TypeError('executor must be a function');
    this.state = PENDING;
    this.value = undefined;
    this.reactions = [];
    this.locked = false;          // resolve-once, independent of state:
                                  // resolve(thenable) locks now, settles later
    try {
      executor((v) => this._resolve(v), (r) => this._reject(r));
    } catch (err) {
      this._reject(err);
    }
  }

  // Spec 2.3: the resolution procedure. Everything interesting lives here.
  _resolve(x) {
    if (this.locked) return;
    this.locked = true;
    if (x === this) return this._settle(REJECTED, new TypeError('Chaining cycle detected'));

    if (x !== null && (typeof x === 'object' || typeof x === 'function')) {
      let then;
      try { then = x.then; } catch (err) { return this._settle(REJECTED, err); }

      if (typeof then === 'function') {
        // Adoption costs two ticks, and that is not an accident: one to run
        // this job, and one more inside x.then() to schedule its reaction.
        // V8 does exactly the same thing, which is why `return somePromise`
        // in a chain is famously two ticks slower than returning a value.
        queueMicrotask(() => {
          let called = false;
          const once = (fn) => (arg) => { if (called) return; called = true; fn(arg); };
          try {
            then.call(x,
              once((v) => { this.locked = false; this._resolve(v); }),  // may be another thenable
              once((r) => this._settle(REJECTED, r)));
          } catch (err) {
            if (!called) { called = true; this._settle(REJECTED, err); }
          }
        });
        return;
      }
    }
    this._settle(FULFILLED, x);
  }

  _reject(r) {
    if (this.locked) return;
    this.locked = true;
    this._settle(REJECTED, r);
  }

  _settle(state, value) {
    if (this.state !== PENDING) return;
    this.state = state;
    this.value = value;
    const reactions = this.reactions;
    this.reactions = [];
    for (const react of reactions) queueMicrotask(() => react(state, value));
  }

  then(onFulfilled, onRejected) {
    const next = new TinyPromise(() => {});
    const react = (state, value) => {
      const handler = state === FULFILLED ? onFulfilled : onRejected;
      if (typeof handler !== 'function') {
        // Pass-through still costs a tick, same as native.
        if (state === FULFILLED) next._resolve(value); else next._reject(value);
        return;
      }
      try { next._resolve(handler(value)); } catch (err) { next._reject(err); }
    };
    if (this.state === PENDING) this.reactions.push(react);
    else {
      const { state, value } = this;
      queueMicrotask(() => react(state, value));   // already settled: still one tick
    }
    return next;
  }

  catch(onRejected) { return this.then(undefined, onRejected); }

  finally(onFinally) {
    return this.then(
      (v) => { onFinally(); return v; },
      (r) => { onFinally(); throw r; });
  }

  static resolve(v) {
    return v instanceof TinyPromise ? v : new TinyPromise((res) => res(v));
  }
  static reject(r) { return new TinyPromise((_, rej) => rej(r)); }

  static all(items) {
    return new TinyPromise((res, rej) => {
      const list = [...items];
      const out = new Array(list.length);
      let left = list.length;
      if (left === 0) return res(out);
      list.forEach((item, i) => TinyPromise.resolve(item).then(
        (v) => { out[i] = v; if (--left === 0) res(out); }, rej));
    });
  }

  static race(items) {
    return new TinyPromise((res, rej) => {
      for (const item of items) TinyPromise.resolve(item).then(res, rej);
    });
  }
}

module.exports = TinyPromise;
