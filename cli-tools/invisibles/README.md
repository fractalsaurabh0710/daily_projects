# invisibles

A lint pass for the characters you cannot see. Point it at files (or pipe text
in) and it reports zero-width joins, bidi overrides, no-break spaces, soft
hyphens, mixed-script words, trailing blanks, stray carriage returns, byte-order
marks and a missing final newline.

```
python3 invisibles.py FILE...
cat something | python3 invisibles.py
python3 invisibles.py --selftest
```

Each finding prints the line with every offender replaced by a stand-in glyph,
plus a caret row underneath:

```
auth.py:4: [risk] zero-width space
  | passZword = secret
  |     ^
auth.py:5: [risk] RLO bidi override
  | if (Baccess)
  |     ^
```

Findings are tagged `[risk]` when the character can silently change what the
text means, and `[note]` when it is merely cosmetic. Exit status is 1 if
anything was reported, so it drops into a pre-commit hook or CI step.

The interesting part is the caret row. Aligning it is normally fiddly, because a
tab is some number of columns wide and a zero-width space is none, so counting
source characters and counting screen columns give different answers. Here every
source character renders to exactly **one** display cell -- tabs become an arrow,
control characters a middle dot, invisibles a single letter -- which makes the
caret row a straight per-character mapping and correct by construction.

Mixed-script detection needs no lookalike table either: the first word of a
character's Unicode name *is* its script, so `unicodedata.name(c).split()[0]`
sorts Cyrillic `с` from Latin `c`, and a word is suspicious when more than one
script appears inside it.

The source is deliberately pure ASCII -- every character it knows about is
spelled as a codepoint -- so `invisibles.py invisibles.py` reports zero findings.
