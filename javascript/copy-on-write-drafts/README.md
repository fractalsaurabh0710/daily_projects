# Copy-on-Write Drafts

`produce(base, recipe)` — mutate a plain object or array as if it were yours,
get back a frozen-in-practice copy that **shares every subtree you did not
touch**. The same idea Immer sells, in ~130 lines of standard-library JavaScript.

## Run

```
node drafts.js
```

Runs its own assertions and prints `all tests passed`.

```js
const { produce } = require('./drafts');

const next = produce(state, (d) => {
  d.user.name = 'grace';
  d.counts.push(4);
});

next.settings === state.settings; // true — untouched, so not copied
```

## The interesting part

A draft is a `Proxy` whose target is an *empty* object of the right shape, not
the original. Reads are answered from the original; the first **write** allocates
a shallow copy and then tells its parent draft to do the same, recursively up to
the root. So a change deep in a tree copies only the spine down to it — siblings
and untouched branches come back identity-equal, which is what makes a
`prev === next` check upstream worth doing.

Two consequences worth noting: writing a value back unchanged is not a change
(`produce` returns the original object, not a clone), and the array `length`
property has to be reported as non-configurable, because a proxy is not allowed
to claim a property is more flexible than the one on its target.
