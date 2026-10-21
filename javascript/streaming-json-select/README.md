# Streaming JSON Select

A JSON parser you feed in chunks of any size, which hands back only the values
matching a path pattern:

```js
const { JsonSelect } = require('./json-select.js');

const p = new JsonSelect('$.items[*].name', (value, path) => console.log(path, value));
p.write('{"items":[{"name":"al');   // chunk boundary inside a string
p.write('pha"},{"name":"beta"}]}');
p.end();
```

Patterns use `.` for keys and `[...]` for indices, with `*` as a wildcard in
either position: `$.items[*].name`, `$.a[0].b`, `$.*`.

## Run

    node test.js

No dependencies; Node's standard library only.

## The interesting part

A recursive-descent parser keeps its position in the input on the JS call
stack, so it cannot stop halfway through a token. This one keeps everything —
the container stack, the half-read string, the pending `\u` escape with two of
its four hex digits — in instance fields, so a chunk may split *anywhere* and
the parse simply continues. The test asserts that: it re-parses the fixture
split at all 229 possible offsets, plus in chunks of 1, 2, 3, 5, 7 and 11
characters, and demands identical output every time.

The second trick is that matching is decided when a container *opens*, not
when it closes. A frame accumulates its children only if its own path fully
matches the pattern, or its parent was already accumulating — so for a leaf
pattern like `$.items[*].name` nothing is ever materialised, and the parser
walks a document of any size in constant memory. The `retained` counter makes
that checkable: it stays at exactly 0 for the leaf pattern over a 500-item
document, and climbs past 500 once the pattern selects the item objects
themselves.
