'use strict';
// A spreadsheet engine in one file: formula parser, dependency graph,
// lazy recalculation of only the cells a change can affect, cycle detection.

/* ---------- A1-style references ---------- */
const REF = /^([A-Z]+)(\d+)$/;
const colNum = c => [...c].reduce((n, ch) => n * 26 + (ch.charCodeAt(0) - 64), 0);
const colName = n => { let s = ''; while (n > 0) { const r = (n - 1) % 26; s = String.fromCharCode(65 + r) + s; n = (n - r - 1) / 26; } return s; };
function expand(a, b) {               // "A1", "B3" -> every ref in the rectangle
  const [, ac, ar] = REF.exec(a), [, bc, br] = REF.exec(b);
  const c1 = Math.min(colNum(ac), colNum(bc)), c2 = Math.max(colNum(ac), colNum(bc));
  const r1 = Math.min(+ar, +br), r2 = Math.max(+ar, +br), out = [];
  for (let r = r1; r <= r2; r++) for (let c = c1; c <= c2; c++) out.push(colName(c) + r);
  return out;
}

/* ---------- lexer ---------- */
const OPS = ['<=', '>=', '<>', '+', '-', '*', '/', '^', '&', '(', ')', ',', ':', '<', '>', '='];
function lex(s) {
  const t = []; let i = 0;
  while (i < s.length) {
    const ch = s[i];
    if (/\s/.test(ch)) { i++; continue; }
    if (/\d/.test(ch) || (ch === '.' && /\d/.test(s[i + 1] || ''))) {
      let j = i; while (j < s.length && /[\d.]/.test(s[j])) j++;
      t.push({ k: 'num', v: parseFloat(s.slice(i, j)) }); i = j; continue;
    }
    if (ch === '"') { let j = i + 1; while (j < s.length && s[j] !== '"') j++; t.push({ k: 'str', v: s.slice(i + 1, j) }); i = j + 1; continue; }
    if (/[A-Za-z_]/.test(ch)) {
      let j = i; while (j < s.length && /[A-Za-z0-9_]/.test(s[j])) j++;
      t.push({ k: 'name', v: s.slice(i, j).toUpperCase() }); i = j; continue;
    }
    const op = OPS.find(o => s.startsWith(o, i));
    if (!op) throw new SyntaxError(`unexpected "${ch}" at ${i}`);
    t.push({ k: op }); i += op.length;
  }
  t.push({ k: 'end' });
  return t;
}

/* ---------- parser (recursive descent, Excel-ish precedence) ---------- */
function parse(src) {
  const t = lex(src); let p = 0;
  const peek = () => t[p].k;
  const eat = k => { if (t[p].k !== k) throw new SyntaxError(`expected ${k}, got ${t[p].k}`); return t[p++]; };

  function cmp() {
    let l = concat();
    while (['<', '>', '<=', '>=', '=', '<>'].includes(peek())) l = { n: 'bin', o: t[p++].k, l, r: concat() };
    return l;
  }
  function concat() { let l = add(); while (peek() === '&') { p++; l = { n: 'bin', o: '&', l, r: add() }; } return l; }
  function add() { let l = mul(); while (peek() === '+' || peek() === '-') { const o = t[p++].k; l = { n: 'bin', o, l, r: mul() }; } return l; }
  function mul() { let l = pow(); while (peek() === '*' || peek() === '/') { const o = t[p++].k; l = { n: 'bin', o, l, r: pow() }; } return l; }
  function pow() { const b = unary(); if (peek() === '^') { p++; return { n: 'bin', o: '^', l: b, r: pow() }; } return b; }
  function unary() { if (peek() === '-') { p++; return { n: 'neg', e: unary() }; } if (peek() === '+') { p++; return unary(); } return primary(); }
  function primary() {
    if (peek() === 'num' || peek() === 'str') return { n: 'lit', v: t[p++].v };
    if (peek() === '(') { p++; const e = cmp(); eat(')'); return e; }
    if (peek() === 'name') {
      const name = t[p++].v;
      if (peek() === '(') {
        p++; const args = [];
        if (peek() !== ')') { args.push(cmp()); while (peek() === ',') { p++; args.push(cmp()); } }
        eat(')'); return { n: 'call', name, args };
      }
      if (!REF.test(name)) throw new SyntaxError(`unknown name ${name}`);
      if (peek() === ':') { p++; const b = eat('name').v; return { n: 'range', a: name, b }; }
      return { n: 'ref', r: name };
    }
    throw new SyntaxError(`unexpected ${peek()}`);
  }
  const ast = cmp(); eat('end'); return ast;
}

/* ---------- values: number | string | {err} | {cells:[]} ---------- */
const err = c => ({ err: c });
const isErr = v => v !== null && typeof v === 'object' && 'err' in v;
function num(v) {
  if (isErr(v)) return v;
  if (typeof v === 'number') return v;
  if (v === '' || v == null) return 0;
  const n = Number(v);
  return Number.isNaN(n) ? err('#VALUE!') : n;
}
function nums(vals) {                 // flatten args/ranges to numbers, blanks dropped
  const out = [];
  for (const v of vals) for (const x of (v && v.cells ? v.cells : [v])) {
    if (x === '' || x == null) continue;
    const n = num(x); if (isErr(n)) return n; out.push(n);
  }
  return out;
}
const sum = a => a.reduce((s, x) => s + x, 0);
const FNS = {
  SUM: a => sum(a), COUNT: a => a.length,
  AVG: a => a.length ? sum(a) / a.length : err('#DIV/0!'),
  MIN: a => a.length ? Math.min(...a) : err('#VALUE!'),
  MAX: a => a.length ? Math.max(...a) : err('#VALUE!'),
  ABS: a => Math.abs(a[0]), SQRT: a => a[0] < 0 ? err('#NUM!') : Math.sqrt(a[0]),
  ROUND: a => { const f = 10 ** (a[1] ?? 0); return Math.round(a[0] * f) / f; },
};

function binop(o, a, b) {
  if (isErr(a)) return a;
  if (isErr(b)) return b;
  if (o === '&') return String(a ?? '') + String(b ?? '');
  if (['<', '>', '<=', '>=', '=', '<>'].includes(o)) {
    let x = num(a), y = num(b);
    if (isErr(x) || isErr(y)) { x = String(a ?? ''); y = String(b ?? ''); }
    return { '<': x < y, '>': x > y, '<=': x <= y, '>=': x >= y, '=': x === y, '<>': x !== y }[o];
  }
  const x = num(a), y = num(b);
  if (isErr(x)) return x;
  if (isErr(y)) return y;
  if (o === '/' && y === 0) return err('#DIV/0!');
  return { '+': x + y, '-': x - y, '*': x * y, '/': x / y, '^': x ** y }[o];
}

/* ---------- the sheet ---------- */
class Sheet {
  constructor() {
    this.src = new Map(); this.ast = new Map(); this.cache = new Map();
    this.deps = new Map(); this.rdeps = new Map(); this.stack = []; this.evals = 0;
  }
  set(ref, text) {
    ref = ref.toUpperCase();
    this.src.set(ref, text);
    if (typeof text === 'string' && text.startsWith('=')) this.ast.set(ref, parse(text.slice(1)));
    else this.ast.delete(ref);
    this.invalidate(ref);
    return this;
  }
  invalidate(ref, seen = new Set()) {         // drop this cell and everything downstream
    if (seen.has(ref)) return;
    seen.add(ref); this.cache.delete(ref);
    for (const r of this.rdeps.get(ref) ?? []) this.invalidate(r, seen);
  }
  link(from, to) {
    if (!from) return;
    (this.deps.get(from) ?? this.deps.set(from, new Set()).get(from)).add(to);
    (this.rdeps.get(to) ?? this.rdeps.set(to, new Set()).get(to)).add(from);
  }
  get(ref) {
    ref = ref.toUpperCase();
    this.link(this.stack[this.stack.length - 1], ref);
    if (this.cache.has(ref)) return this.cache.get(ref);
    if (this.stack.includes(ref)) return err('#CYCLE!');   // never cached: stack-dependent
    const ast = this.ast.get(ref);
    if (!ast) { const v = this.src.get(ref); return v === undefined ? '' : v; }
    for (const t of this.deps.get(ref) ?? []) this.rdeps.get(t)?.delete(ref);
    this.deps.set(ref, new Set());
    this.stack.push(ref); this.evals++;
    let v;
    try { v = this.evaluate(ast); } catch (e) { v = err('#ERROR!'); } finally { this.stack.pop(); }
    if (v && v.cells) v = v.cells[0] ?? '';
    this.cache.set(ref, v);
    return v;
  }
  evaluate(node) {
    switch (node.n) {
      case 'lit': return node.v;
      case 'ref': return this.get(node.r);
      case 'range': return { cells: expand(node.a, node.b).map(r => this.get(r)) };
      case 'neg': { const v = num(this.evaluate(node.e)); return isErr(v) ? v : -v; }
      case 'bin': return binop(node.o, this.evaluate(node.l), this.evaluate(node.r));
      case 'call': {
        if (node.name === 'IF') {
          const c = this.evaluate(node.args[0]);
          if (isErr(c)) return c;
          const t = typeof c === 'number' ? c !== 0 : typeof c === 'boolean' ? c : c !== '';
          return this.evaluate(node.args[t ? 1 : 2] ?? { n: 'lit', v: '' });
        }
        const fn = FNS[node.name];
        if (!fn) return err('#NAME?');
        const a = nums(node.args.map(x => this.evaluate(x)));
        return isErr(a) ? a : fn(a);
      }
    }
  }
}

module.exports = { Sheet, parse };

/* ---------- tests ---------- */
if (require.main === module) {
  const assert = require('assert');
  const s = new Sheet();

  // precedence, unary minus, right-associative ^
  s.set('A1', '=2+3*4').set('A2', '=(2+3)*4').set('A3', '=2^3^2').set('A4', '=-3^2');
  assert.strictEqual(s.get('A1'), 14);
  assert.strictEqual(s.get('A2'), 20);
  assert.strictEqual(s.get('A3'), 512);
  assert.strictEqual(s.get('A4'), 9);

  // ranges and functions
  [1, 2, 3, 4].forEach((v, i) => s.set('B' + (i + 1), v));
  s.set('C1', '=SUM(B1:B4)').set('C2', '=AVG(B1:B4)').set('C3', '=MAX(B1:B4)-MIN(B1:B4)');
  assert.strictEqual(s.get('C1'), 10);
  assert.strictEqual(s.get('C2'), 2.5);
  assert.strictEqual(s.get('C3'), 3);
  s.set('C4', '=ROUND(AVG(B1:B4)*3,1)');
  assert.strictEqual(s.get('C4'), 7.5);

  // text, comparison, IF
  s.set('D1', 'ok').set('D2', '=IF(C1>5,"big","small")').set('D3', '=D1&"!"');
  assert.strictEqual(s.get('D2'), 'big');
  assert.strictEqual(s.get('D3'), 'ok!');

  // errors propagate through arithmetic
  s.set('E1', '=1/0').set('E2', '=E1+1').set('E3', '=NOPE(1)').set('E4', '=SQRT(-1)');
  assert.deepStrictEqual(s.get('E2'), { err: '#DIV/0!' });
  assert.deepStrictEqual(s.get('E3'), { err: '#NAME?' });
  assert.deepStrictEqual(s.get('E4'), { err: '#NUM!' });

  // cycles, direct and indirect, and recovery once broken
  s.set('F1', '=F2').set('F2', '=F1');
  assert.deepStrictEqual(s.get('F1'), { err: '#CYCLE!' });
  s.set('G1', '=G2').set('G2', '=G3').set('G3', '=G1+1');
  assert.deepStrictEqual(s.get('G1'), { err: '#CYCLE!' });
  s.set('G3', 7);
  assert.strictEqual(s.get('G1'), 7);

  // the claim: a change recomputes only the cells downstream of it
  const t = new Sheet();
  t.set('A1', 1).set('B1', '=A1*2').set('C1', '=B1+10').set('Z1', '=99*2');
  assert.strictEqual(t.get('C1'), 12);
  assert.strictEqual(t.get('Z1'), 198);
  const before = t.evals;
  t.set('A1', 5);
  assert.strictEqual(t.get('C1'), 20);
  assert.strictEqual(t.evals - before, 2, 'only B1 and C1 should recompute');
  assert.strictEqual(t.get('Z1'), 198);
  assert.strictEqual(t.evals - before, 2, 'Z1 should still be cached');

  // dependencies are re-discovered, not remembered: C1 no longer reads B1
  t.set('C1', '=A1+1');
  assert.strictEqual(t.get('C1'), 6);
  const n = t.evals;
  t.set('B1', '=A1*100');
  t.get('C1');
  assert.strictEqual(t.evals, n, 'C1 must not be invalidated by a cell it stopped reading');

  console.log('all tests passed (' + (t.evals + s.evals) + ' formula evaluations)');
}
