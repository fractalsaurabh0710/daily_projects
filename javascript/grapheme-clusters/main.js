'use strict';

// Three answers to "how long is this string?", and a grapheme segmenter built
// from UAX #29's break rules to produce the third one -- checked, character for
// character, against Intl.Segmenter.

const RE_EXTEND = /^[\p{Mn}\p{Me}]$/u;
const RE_SPACINGMARK = /^\p{Mc}$/u;
const RE_EXTPICT = /^\p{Extended_Pictographic}$/u;
const RE_CONTROL = /^[\p{Cc}\p{Cf}\p{Zl}\p{Zp}\p{Cs}]$/u;

// Extend is Grapheme_Extend, which is NOT the same as "is a combining mark".
// Skin-tone modifiers are Sk, ZWNJ is Cf, and a handful of Indic vowel signs
// are Mc -- all of them break as Extend anyway.
const EXTEND_EXTRA = new Set([0x200c, 0x09be, 0x09d7, 0x0b3e, 0x0b57, 0x0bbe,
  0x0bd7, 0x0cc2, 0x0cd5, 0x0cd6, 0x0d3e, 0x0d57, 0x0dcf, 0x0ddf, 0x1b35,
  0x1f3fb, 0x1f3fc, 0x1f3fd, 0x1f3fe, 0x1f3ff]);
// GB9c (new in Unicode 15.1): an Indic consonant joined through a virama to
// another consonant is one cluster. Without this rule a Devanagari conjunct
// splits in the middle, which is what every pre-15.1 segmenter did.
const LINKER = new Set([0x094d, 0x09cd, 0x0acd, 0x0b4d, 0x0c4d, 0x0d4d]);
const RE_INCB_CONSONANT = /^\p{Lo}$/u;
// InCB=Extend is not simply "Extend or ZWJ". ZWNJ is excluded, which is the
// whole point of ZWNJ in Indic text: it asks for the half form instead of the
// conjunct, so it severs the chain GB9c is looking for even though it is an
// Extend character sitting in exactly the right place.
const INCB_NONE = new Set([0x200c]);
const RE_INCB_SCRIPT = /^[\p{Script=Devanagari}\p{Script=Bengali}\p{Script=Gujarati}\p{Script=Malayalam}\p{Script=Oriya}\p{Script=Telugu}]$/u;
const isConsonant = (ch) => RE_INCB_CONSONANT.test(ch) && RE_INCB_SCRIPT.test(ch);

// Thai/Lao SARA AM are gc=Lo, not marks at all, yet they break as SpacingMark.
// Nothing about their general category predicts it; they are listed by hand in
// the standard, so they have to be listed by hand here too.
const SPACINGMARK_EXTRA = new Set([0x0e33, 0x0eb3]);
const PREPEND = new Set([0x0600, 0x0601, 0x0602, 0x0603, 0x0604, 0x0605, 0x06dd,
  0x070f, 0x0890, 0x0891, 0x08e2, 0x110bd, 0x110cd]);

function inRange(cp, lo, hi) { return cp >= lo && cp <= hi; }

function cls(ch) {
  const cp = ch.codePointAt(0);
  if (cp === 0x0d) return 'CR';
  if (cp === 0x0a) return 'LF';
  if (cp === 0x200d) return 'ZWJ';
  if (EXTEND_EXTRA.has(cp)) return 'Extend';
  if (PREPEND.has(cp)) return 'Prepend';
  if (inRange(cp, 0x1f1e6, 0x1f1ff)) return 'RI';
  if (inRange(cp, 0x1100, 0x115f) || inRange(cp, 0xa960, 0xa97c)) return 'L';
  if (inRange(cp, 0x1160, 0x11a7) || inRange(cp, 0xd7b0, 0xd7c6)) return 'V';
  if (inRange(cp, 0x11a8, 0x11ff) || inRange(cp, 0xd7cb, 0xd7fb)) return 'T';
  if (inRange(cp, 0xac00, 0xd7a3)) return (cp - 0xac00) % 28 === 0 ? 'LV' : 'LVT';
  if (SPACINGMARK_EXTRA.has(cp)) return 'SpacingMark';
  if (RE_EXTEND.test(ch)) return 'Extend';
  if (RE_CONTROL.test(ch)) return 'Control';
  if (RE_SPACINGMARK.test(ch)) return 'SpacingMark';
  if (RE_EXTPICT.test(ch)) return 'ExtPict';
  return 'Other';
}

const HANGUL_OK = {
  L: new Set(['L', 'V', 'LV', 'LVT']),
  LV: new Set(['V', 'T']), V: new Set(['V', 'T']),
  LVT: new Set(['T']), T: new Set(['T']),
};

function graphemes(str) {
  const chars = [...str];
  if (chars.length === 0) return [];
  const out = [];
  let start = 0;
  let a = cls(chars[0]);
  let riOdd = a === 'RI';
  let pictExtend = a === 'ExtPict';   // prev run matches ExtPict Extend*
  let zwjAfterPict = false;           // prev run matches ExtPict Extend* ZWJ
  let consRun = isConsonant(chars[0]); // prev run is Consonant [Extend|Linker]*
  let linkerSeen = false;              // ...and contains at least one Linker

  for (let i = 1; i < chars.length; i++) {
    const b = cls(chars[i]);
    let brk;
    if (a === 'CR' && b === 'LF') brk = false;                      // GB3
    else if (a === 'CR' || a === 'LF' || a === 'Control') brk = true; // GB4
    else if (b === 'CR' || b === 'LF' || b === 'Control') brk = true; // GB5
    else if (HANGUL_OK[a] && HANGUL_OK[a].has(b)) brk = false;       // GB6-8
    else if (b === 'Extend' || b === 'ZWJ') brk = false;             // GB9
    else if (b === 'SpacingMark') brk = false;                       // GB9a
    else if (a === 'Prepend') brk = false;                           // GB9b
    else if (consRun && linkerSeen && isConsonant(chars[i])) brk = false; // GB9c
    else if (zwjAfterPict && b === 'ExtPict') brk = false;           // GB11
    else if (a === 'RI' && b === 'RI' && riOdd) brk = false;          // GB12/13
    else brk = true;                                                 // GB999

    if (brk) { out.push(chars.slice(start, i).join('')); start = i; }

    if (b === 'ExtPict') { pictExtend = true; zwjAfterPict = false; }
    else if (b === 'Extend' && pictExtend) { zwjAfterPict = false; }
    else if (b === 'ZWJ' && pictExtend) { pictExtend = false; zwjAfterPict = true; }
    else { pictExtend = false; zwjAfterPict = false; }
    riOdd = b === 'RI' ? !riOdd : false;
    const cp = chars[i].codePointAt(0);
    if (isConsonant(chars[i])) { consRun = true; linkerSeen = false; }
    else if (consRun && LINKER.has(cp)) linkerSeen = true;
    else if (!(consRun && (b === 'ZWJ' || b === 'Extend') && !INCB_NONE.has(cp))) { consRun = false; linkerSeen = false; }
    a = b;
  }
  out.push(chars.slice(start).join(''));
  return out;
}

// ---------------------------------------------------------------- verification

const native = (s) => [...new Intl.Segmenter().segment(s)].map((x) => x.segment);
const esc = (s) => [...s].map((c) => {
  const cp = c.codePointAt(0);
  return cp > 0x20 && cp < 0x7f ? c : 'U+' + cp.toString(16).toUpperCase().padStart(4, '0');
}).join(' ');

const CASES = [
  ['café', 'combining acute'],
  ['नमस्ते', 'devanagari namaste'],
  ['한국어', 'hangul syllables + conjoining jamo'],
  ['👩‍👩‍👧‍👦', 'family via ZWJ'],
  ['🇮🇳🇺🇸', 'two flags'],
  ['🇮🇳🇺', 'flag + orphan RI'],
  ['👍🏽', 'thumbs up + skin tone'],
  ['1️⃣', 'keycap'],
  ['a\r\nb', 'CRLF'],
  ['🏳️‍🌈', 'rainbow flag'],
  ['क्ष', 'devanagari ksha conjunct'],
  ['ক্ষ', 'bengali kssa conjunct'],
  ['क्', 'trailing virama, no consonant'],
  ['กำ', 'thai sara am (gc=Lo, breaks as SpacingMark)'],
  ['ष⃣्ष', 'keycap does not sever the chain'],
  ['क्‌ष', 'ZWNJ does sever it'],
];

let bad = 0;
console.log('string                     UTF-16  code pts  graphemes  native');
console.log('-'.repeat(72));
for (const [s, label] of CASES) {
  const mine = graphemes(s);
  const ref = native(s);
  const ok = mine.length === ref.length && mine.every((g, i) => g === ref[i]);
  if (!ok) { bad++; console.log('  MISMATCH', label, '\n    mine:', mine.map(esc), '\n    ref: ', ref.map(esc)); }
  console.log(
    label.padEnd(26),
    String(s.length).padStart(6),
    String([...s].length).padStart(10),
    String(mine.length).padStart(10),
    String(ref.length).padStart(7), ok ? '' : '  <-- differs');
}

// Fuzz: assemble random sequences from every class the rules talk about.
const POOL = ['a', 'é'.slice(1), 'न', '्', 'े', 'ᄀ',
  'ᅡ', 'ᆨ', '한', '핬', '‍', '‌', '️',
  '👩', '🇮', '🇳', '🏽', '⃣',
  'क', 'ष', 'ক', '্',
  '\r', '\n', '\u0009', '؀', 'ำ', ' '];
let rng = 1234567;
// Low bits of a power-of-two-modulus LCG cycle with tiny period, so %n on the
// raw value silently never emits some combinations -- take the high bits.
const rand = (n) => (((rng = (rng * 1103515245 + 12345) & 0x7fffffff) >>> 12) % n);

let trials = 0, agree = 0;
const diffs = new Map();
for (let t = 0; t < 50000; t++) {
  let s = '';
  const n = 1 + rand(8);
  for (let i = 0; i < n; i++) s += POOL[rand(POOL.length)];
  const mine = graphemes(s).join('|');
  const ref = native(s).join('|');
  trials++;
  if (mine === ref) agree++;
  else {
    const key = [...s].map((c) => cls(c)).join(' ');
    diffs.set(key, (diffs.get(key) || 0) + 1);
  }
}

console.log('\nhand-picked cases:', CASES.length - bad, '/', CASES.length, 'match Intl.Segmenter');
console.log('fuzz:', agree, '/', trials, `agree (${(100 * agree / trials).toFixed(2)}%)`);
if (diffs.size) {
  console.log('most common disagreeing class sequences:');
  [...diffs].sort((x, y) => y[1] - x[1]).slice(0, 5)
    .forEach(([k, v]) => console.log('  ' + String(v).padStart(4), k));
}

const fam = CASES[3][0];
console.log(`\nOne family emoji: ${fam.length} UTF-16 units, ${[...fam].length} code points, ${graphemes(fam).length} grapheme.`);
console.log(`Reversing by code point gives: ${[...fam].reverse().join('')}`);
console.log(`Reversing by grapheme gives:   ${graphemes(fam).reverse().join('')}`);

if (bad) { console.error('\nFAIL: hand-picked case mismatch'); process.exit(1); }
console.log('\nOK');
