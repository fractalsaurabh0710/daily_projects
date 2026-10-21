'use strict';
// A resumable JSON parser that pulls out only the values matching a path
// pattern. Chunks may split anywhere -- mid-string, mid-number, mid-escape --
// because every token lives in the parser's state, not on the JS call stack.
// Subtrees that cannot match are parsed and thrown away, never materialised.

function parsePattern(src) {
  const out = [];
  let i = src.startsWith('$') ? 1 : 0;
  while (i < src.length) {
    const c = src[i];
    if (c === '.') { i += 1; continue; }
    if (c === '[') {
      const j = src.indexOf(']', i);
      if (j < 0) throw new SyntaxError('unclosed [ in pattern');
      const raw = src.slice(i + 1, j).trim();
      out.push(raw === '*' ? '*' : Number(raw));
      i = j + 1;
      continue;
    }
    let j = i;
    while (j < src.length && src[j] !== '.' && src[j] !== '[') j += 1;
    out.push(src.slice(i, j));
    i = j;
  }
  return out;
}

const segEq = (seg, key) => seg === '*' || String(seg) === String(key);

function matchFull(path, pat) {
  if (path.length !== pat.length) return false;
  return pat.every((seg, i) => segEq(seg, path[i]));
}

const WS = new Set([' ', '\t', '\n', '\r']);
const NUMCHAR = /[-+0-9.eE]/;
const NUMBER = /^-?(0|[1-9][0-9]*)(\.[0-9]+)?([eE][-+]?[0-9]+)?$/;
const ESCAPES = { '"': '"', '\\': '\\', '/': '/', b: '\b', f: '\f', n: '\n', r: '\r', t: '\t' };

class JsonSelect {
  constructor(pattern, onMatch) {
    this.pat = parsePattern(pattern);
    this.onMatch = onMatch;
    this.stack = [];
    this.mode = 'value';
    this.buf = '';
    this.esc = false;
    this.hex = null;
    this.isKey = false;
    this.retained = 0; // values held for accumulation; the pruning claim
    this.finished = false;
  }

  write(chunk) {
    for (const c of String(chunk)) this._char(c);
    return this;
  }

  end() {
    if (this.mode === 'number') this._number();
    else if (this.mode === 'literal') this._literal();
    if (!this.finished) throw new SyntaxError('unexpected end of JSON input');
    return this;
  }

  _path() {
    return this.stack.map((f) => (f.arr ? f.index : f.key));
  }

  _open(arr) {
    const parent = this.stack[this.stack.length - 1];
    const keep = (parent ? parent.keep : false) || matchFull(this._path(), this.pat);
    this.stack.push({ arr, keep, value: keep ? (arr ? [] : {}) : null, key: null, index: 0 });
    this.mode = arr ? 'value' : 'key';
  }

  _close() {
    const f = this.stack.pop();
    this._emit(f.value, f.keep);
  }

  _emit(value, have = true) {
    const path = this._path();
    if (have && matchFull(path, this.pat)) this.onMatch(value, path);
    const top = this.stack[this.stack.length - 1];
    if (!top) { this.finished = true; this.mode = 'done'; return; }
    if (top.keep) {
      if (top.arr) top.value.push(value); else top.value[top.key] = value;
      this.retained += 1;
    }
    if (top.arr) top.index += 1;
    this.mode = 'comma';
  }

  _number() {
    if (!NUMBER.test(this.buf)) throw new SyntaxError('bad number ' + JSON.stringify(this.buf));
    const v = Number(this.buf);
    this.buf = '';
    this._emit(v);
  }

  _literal() {
    const v = { true: true, false: false, null: null }[this.buf];
    if (v === undefined) throw new SyntaxError('bad literal ' + JSON.stringify(this.buf));
    this.buf = '';
    this._emit(v);
  }

  _char(c) {
    const top = this.stack[this.stack.length - 1];
    switch (this.mode) {
      case 'string': return this._string(c);
      case 'number':
        if (NUMCHAR.test(c)) { this.buf += c; return; }
        this._number();
        return this._char(c);
      case 'literal':
        if (c >= 'a' && c <= 'z') { this.buf += c; return; }
        this._literal();
        return this._char(c);
      case 'value':
        if (WS.has(c)) return;
        if (c === '{') return this._open(false);
        if (c === '[') return this._open(true);
        if (c === '"') { this.mode = 'string'; this.isKey = false; this.buf = ''; return; }
        if (c === '-' || (c >= '0' && c <= '9')) { this.mode = 'number'; this.buf = c; return; }
        if (c >= 'a' && c <= 'z') { this.mode = 'literal'; this.buf = c; return; }
        if (c === ']' && top && top.arr && top.index === 0) return this._close();
        throw new SyntaxError('unexpected ' + JSON.stringify(c) + ' where a value was expected');
      case 'key':
        if (WS.has(c)) return;
        if (c === '"') { this.mode = 'string'; this.isKey = true; this.buf = ''; return; }
        if (c === '}' && top && top.key === null) return this._close();
        throw new SyntaxError('unexpected ' + JSON.stringify(c) + ' where a key was expected');
      case 'colon':
        if (WS.has(c)) return;
        if (c === ':') { this.mode = 'value'; return; }
        throw new SyntaxError('expected ":"');
      case 'comma':
        if (WS.has(c)) return;
        if (c === ',') { this.mode = top.arr ? 'value' : 'key'; if (!top.arr) top.key = null; return; }
        if ((c === '}' && !top.arr) || (c === ']' && top.arr)) return this._close();
        throw new SyntaxError('expected "," or a close bracket');
      default:
        if (WS.has(c)) return;
        throw new SyntaxError('trailing content after the top-level value');
    }
  }

  _string(c) {
    if (this.hex !== null) {
      this.hex += c;
      if (this.hex.length < 4) return;
      if (!/^[0-9a-fA-F]{4}$/.test(this.hex)) throw new SyntaxError('bad \\u escape');
      this.buf += String.fromCharCode(parseInt(this.hex, 16));
      this.hex = null;
      return;
    }
    if (this.esc) {
      this.esc = false;
      if (c === 'u') { this.hex = ''; return; }
      if (!(c in ESCAPES)) throw new SyntaxError('bad escape \\' + c);
      this.buf += ESCAPES[c];
      return;
    }
    if (c === '\\') { this.esc = true; return; }
    if (c !== '"') { this.buf += c; return; }
    const s = this.buf;
    this.buf = '';
    if (this.isKey) { this.stack[this.stack.length - 1].key = s; this.mode = 'colon'; return; }
    this._emit(s);
  }
}

function select(text, pattern, chunkSize = Infinity) {
  const hits = [];
  const p = new JsonSelect(pattern, (value, path) => hits.push({ value, path }));
  if (chunkSize === Infinity) p.write(text);
  else for (let i = 0; i < text.length; i += chunkSize) p.write(text.slice(i, i + chunkSize));
  p.end();
  return hits;
}

module.exports = { JsonSelect, select, parsePattern };
