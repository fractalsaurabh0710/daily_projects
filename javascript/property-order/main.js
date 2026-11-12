// Property order in JavaScript objects, reimplemented from the spec.
//
// Objects are not insertion-ordered. OrdinaryOwnPropertyKeys lists integer-index
// keys first in ASCENDING NUMERIC order, then the remaining string keys in
// creation order, then symbols in creation order. The model below reproduces
// that from nothing but the insertion sequence, and is checked against the
// engine on randomly built objects.

const assert = require("node:assert");

const UINT32_MAX = 2 ** 32 - 1;

// A string key is an "array index" iff ToString(ToUint32(P)) is P and the value
// is not 2**32-1. So the key must be in canonical numeric form -- "01", "1.0",
// "-0" and " 1" are all ordinary strings -- and 4294967295 itself is excluded,
// while 4294967294 is not.
function isArrayIndex(key) {
  if (typeof key !== "string") return false;
  const n = Number(key);
  if (!Number.isInteger(n) || n < 0 || n >= UINT32_MAX) return false;
  return String(n) === key;
}

// The prediction: indices sorted, then strings as inserted, then symbols.
function predictOwnKeys(insertionOrder) {
  const indices = [];
  const strings = [];
  const symbols = [];
  for (const key of insertionOrder) {
    if (typeof key === "symbol") symbols.push(key);
    else if (isArrayIndex(key)) indices.push(key);
    else strings.push(key);
  }
  indices.sort((a, b) => Number(a) - Number(b));
  return [...indices, ...strings, ...symbols];
}

function build(keys) {
  const obj = {};
  for (const key of keys) obj[key] = true;
  return obj;
}

// ---------------------------------------------------------------- edge cases

const edge = [
  ["2", true],
  ["0", true],
  ["4294967294", true], // the largest array index there is
  ["4294967295", false], // 2**32-1: reserved as a length, never an index
  ["01", false], // not canonical
  ["1.0", false], // not canonical
  ["-0", false], // ToString(ToUint32("-0")) is "0"
  ["-1", false],
  ["1e21", false], // canonical, but far past the limit
  ["Infinity", false],
  [" 1", false],
  ["", false],
];
for (const [key, expected] of edge) {
  assert.strictEqual(isArrayIndex(key), expected, `isArrayIndex(${JSON.stringify(key)})`);
  // Confirm it against the engine: an index key must sort ahead of "z".
  const keys = Reflect.ownKeys(build(["z", key]));
  assert.strictEqual(keys[0] === key, expected, `engine disagrees on ${JSON.stringify(key)}`);
}

// The headline case: inserted backwards, read out forwards.
assert.deepStrictEqual(Reflect.ownKeys(build(["3", "1", "2"])), ["1", "2", "3"]);
// And a string key keeps its place no matter what it looks like next to one.
assert.deepStrictEqual(Reflect.ownKeys(build(["b", "2", "a", "1"])), ["1", "2", "b", "a"]);

// ------------------------------------------------------- randomised checking

function randomKeys(rand, count) {
  const pool = [];
  for (let i = 0; i < count; i++) {
    const roll = rand() * 100;
    if (roll < 40) pool.push(String(Math.floor(rand() * 50)));
    else if (roll < 55) pool.push(String(Math.floor(rand() * UINT32_MAX)));
    else if (roll < 65) pool.push(["01", "1.0", "-0", "-7", "1e21", "4294967295"][Math.floor(rand() * 6)]);
    else if (roll < 90) pool.push("k" + Math.floor(rand() * 50));
    else pool.push(Symbol("s" + i));
  }
  return [...new Set(pool)];
}

let seed = 20261112;
const rand = () => ((seed = (seed * 1103515245 + 12345) & 0x7fffffff) / 0x80000000);

const show = (keys) => keys.map((k) => (typeof k === "symbol" ? k.toString() : k)).join(",");

let reordered = 0;
const TRIALS = 4000;
for (let t = 0; t < TRIALS; t++) {
  const keys = randomKeys(rand, 1 + Math.floor(rand() * 12));
  const actual = Reflect.ownKeys(build(keys));
  assert.deepStrictEqual(actual, predictOwnKeys(keys), `trial ${t}: ${show(keys)}`);
  if (show(actual) !== show(keys)) reordered++;
}

// Deleting a string key and putting it back moves it to the end of the string
// run. Doing the same to an index key changes nothing at all, because its
// position is computed from its value rather than remembered.
const obj = build(["1", "2", "a", "b"]);
delete obj.a;
obj.a = true;
assert.deepStrictEqual(Reflect.ownKeys(obj), ["1", "2", "b", "a"]);
delete obj["1"];
obj["1"] = true;
assert.deepStrictEqual(Reflect.ownKeys(obj), ["1", "2", "b", "a"]);

// A Map is the thing that actually keeps insertion order: its keys are values,
// not property names, so "1" and 1 are two different entries and neither sorts.
const map = new Map([["3", "x"], ["1", "y"], [1, "z"]]);
assert.deepStrictEqual([...map.keys()], ["3", "1", 1]);

console.log("edge cases:   %d key forms classified and confirmed against the engine", edge.length);
console.log("random:       %d objects, every key order predicted exactly", TRIALS);
console.log("reordered:    %d of %d objects came out in an order other than insertion", reordered, TRIALS);
console.log("largest index: 4294967294 sorts; 4294967295 does not and stays where it was put");
