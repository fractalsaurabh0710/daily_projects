# Grapheme Clusters

How long is `"👩‍👩‍👧‍👦"`? JavaScript gives three different answers — 11, 7, and 1 —
and only the last one is the number of things on the screen. The first two are
free (`.length`, `[...s].length`); the third needs UAX #29's grapheme break
rules, which is what this implements, then checks character for character
against `Intl.Segmenter`.

## Running it

    node main.js

No dependencies. Needs Node 18+ for `Intl.Segmenter` (used only as the oracle —
the segmenter itself is built from the rules, not from it).

It prints the three lengths for 16 hand-picked strings, then fuzzes 50,000
random sequences assembled from every character class the rules mention. All 16
cases and all 50,000 sequences currently match `Intl.Segmenter` exactly.

## What was interesting

Three of the rules cannot be inferred from a character's general category, and
each one was found by the fuzzer rather than by reading:

- **U+0E33 THAI SARA AM is `gc=Lo`** — not a mark of any kind — yet it breaks as
  `SpacingMark`, so it joins the character before it. Classifying by general
  category alone disagrees with ICU on 10% of random sequences containing it.
- **Skin-tone modifiers are `gc=Sk`**, and ZWNJ is `gc=Cf`, but both are
  `Extend`. "Is it a combining mark" is the wrong question; `Grapheme_Extend` is
  a property in its own right.
- **GB9c, added in Unicode 15.1**, joins an Indic consonant to the next one
  through a virama, so `नमस्ते` is 3 clusters rather than 4. The chain it looks
  for is `Consonant [InCB=Extend]* Linker [InCB=Extend]* × Consonant`, and
  `InCB=Extend` is deliberately *not* "Extend or ZWJ": ZWNJ is excluded, because
  asking for the half form instead of the conjunct is exactly what ZWNJ is for.
  A combining keycap wedged into the same position does *not* sever the chain.

The fuzzer also found a bug in itself. It drew from the pool with
`(lcg_state & 0x7fffffff) % n`, and the low bits of a power-of-two-modulus LCG
cycle with a very short period — so some character combinations were never
generated at all, and the first version reported 100% agreement on 20,000
sequences while being wrong about Devanagari. Taking the high bits instead
(`>>> 12`) dropped agreement to 88% immediately.

## Known gap

`Extend` and `SpacingMark` are derived from general category plus a hand-listed
set of exceptions. Only the exceptions the fuzz pool exercises are listed here,
so a character outside that pool may still be misclassified; the fix in each
case is one more entry in one of the two sets, not a change to the rules.
