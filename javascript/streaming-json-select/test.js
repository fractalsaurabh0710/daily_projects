'use strict';
const assert = require('assert');
const { JsonSelect, select, parsePattern } = require('./json-select.js');

const DOC = JSON.stringify({
  meta: { count: 3, ok: true, note: 'café — "quoted"\n' },
  items: [
    { id: 1, name: 'alpha', tags: ['x', 'y'], score: -1.5e2 },
    { id: 2, name: 'beta', tags: [], score: 0 },
    { id: 3, name: 'gamma', tags: ['z'], score: 12.25 },
  ],
  empty: {},
});

const names = (text, chunk) => select(text, '$.items[*].name', chunk).map((h) => h.value);

// 1. patterns
assert.deepStrictEqual(parsePattern('$.items[*].name'), ['items', '*', 'name']);
assert.deepStrictEqual(parsePattern('a[0].b'), ['a', 0, 'b']);

// 2. selection, paths, and types survive the round trip
assert.deepStrictEqual(names(DOC), ['alpha', 'beta', 'gamma']);
assert.deepStrictEqual(select(DOC, '$.items[1].id')[0], { value: 2, path: ['items', 1, 'id'] });
assert.deepStrictEqual(select(DOC, '$.items[*].score').map((h) => h.value), [-150, 0, 12.25]);
assert.deepStrictEqual(select(DOC, '$.meta.ok')[0].value, true);
assert.deepStrictEqual(select(DOC, '$.meta.note')[0].value, 'café — "quoted"\n');
assert.deepStrictEqual(select(DOC, '$.empty')[0].value, {});
assert.deepStrictEqual(select(DOC, '$.items[*].tags[*]').map((h) => h.value), ['x', 'y', 'z']);
assert.deepStrictEqual(select(DOC, '$.items[0]')[0].value, JSON.parse(DOC).items[0]);
assert.deepStrictEqual(select('  42  ', '$')[0].value, 42);
assert.deepStrictEqual(select('[]', '$')[0].value, []);
assert.deepStrictEqual(select(DOC, '$.*').length, 3);

// 3. the resumability claim: every possible split gives the same answer
for (let cut = 0; cut <= DOC.length; cut += 1) {
  const hits = [];
  const q = new JsonSelect('$.items[*].name', (v) => hits.push(v));
  q.write(DOC.slice(0, cut)).write(DOC.slice(cut)).end();
  assert.deepStrictEqual(hits, ['alpha', 'beta', 'gamma'], 'split at ' + cut);
}
for (const size of [1, 2, 3, 5, 7, 11]) {
  assert.deepStrictEqual(names(DOC, size), ['alpha', 'beta', 'gamma'], 'chunks of ' + size);
}

// 4. the pruning claim: nothing is accumulated for a leaf pattern
const big = JSON.stringify({ items: Array.from({ length: 500 }, (_, i) => ({ id: i, name: 'n' + i, blob: Array.from({ length: 20 }, (_, j) => j) })) });
const leaf = new JsonSelect('$.items[*].name', () => {});
leaf.write(big).end();
assert.strictEqual(leaf.retained, 0, 'leaf pattern must retain nothing');

const whole = new JsonSelect('$.items[*]', () => {});
whole.write(big).end();
assert.ok(whole.retained > 500, 'selecting containers does retain their contents');
assert.ok(JSON.parse(big).items.length === 500);

// 5. malformed input is rejected
for (const bad of ['{', '{"a"}', '{"a":}', '[1,]', '{"a":1}}', 'tru', '01', '"unterminated']) {
  assert.throws(() => select(bad, '$'), SyntaxError, JSON.stringify(bad) + ' should throw');
}

// 6. agreement with JSON.parse over the whole document
const roots = select(DOC, '$');
assert.deepStrictEqual(roots[0].value, JSON.parse(DOC));

console.log('all tests passed');
