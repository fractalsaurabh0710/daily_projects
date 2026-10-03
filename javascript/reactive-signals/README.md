# Reactive Signals

A fine-grained reactivity core in ~120 lines of plain JavaScript — `signal`,
`computed`, `effect`, `batch`, `untrack` — with no dependencies and no build
step. This is the mechanism behind Solid, Vue's `ref`/`computed`, and Preact
signals, stripped to the part that actually does the work.

```
node test.js
```

Nine assertions covering caching, laziness, batching, disposal, and dependency
rediscovery. No test runner needed.

```js
import { signal, computed, effect } from './signals.js';

const [price, setPrice] = signal(10);
const [qty, setQty] = signal(2);
const total = computed(() => price() * qty());

effect(() => console.log('total:', total()));  // total: 20
setQty(3);                                     // total: 30
```

## The one interesting bit

There is no dependency array anywhere. A module-level `ACTIVE` variable holds
whichever computation is currently executing; reading a signal inside one
records the edge in both directions. Before a computation re-runs it unlinks
every dependency it had, so the graph is rebuilt from scratch each time — which
is why a conditional branch that stops being taken also stops firing, with no
bookkeeping. The `dead branches` test pins that behaviour down.

`computed` is lazy rather than eager: a write marks it stale and propagates
staleness, but the function only runs on the next read.

Unfinished: a stale computed still wakes its dependent effects even when
recomputing yields the same value — real implementations push the equality
check down into the computed to cut that off.
