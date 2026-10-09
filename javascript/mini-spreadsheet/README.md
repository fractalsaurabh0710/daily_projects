# Mini Spreadsheet

A spreadsheet engine in one file: an Excel-ish formula language, a dependency
graph built from what formulas actually read, and recalculation limited to the
cells a change can reach.

```
node sheet.js      # runs the test suite
```

Or use it as a module:

```js
const { Sheet } = require('./sheet');
const s = new Sheet();
s.set('A1', 3).set('A2', 4).set('B1', '=SQRT(A1^2+A2^2)');
s.get('B1');  // 5
```

Supports numbers, text, `A1` references, `A1:B3` ranges, `+ - * / ^ &`,
comparisons, and `SUM AVG MIN MAX COUNT ABS SQRT ROUND IF`. Errors are values
(`{err:'#DIV/0!'}`) so they propagate through arithmetic the way a real
spreadsheet's do.

The interesting part is that the dependency edges are a side effect of
evaluation rather than something parsed out of the formula: `get()` pushes the
cell being computed onto a stack, and every reference read while it is there
records an edge. That buys three things at once for almost no code. Stale edges
vanish, because a cell's out-edges are cleared before it recomputes — so a
formula that stops reading `B1` genuinely stops depending on it. Invalidation is
a walk over the reverse edges, so editing one cell drops exactly its downstream
cache. And a cycle is just a reference to something already on the stack, which
makes `#CYCLE!` the one value never cached — it is a fact about the evaluation
in progress, not about the cell. The tests assert each of those, including
counting evaluations to prove untouched cells are not recomputed.
