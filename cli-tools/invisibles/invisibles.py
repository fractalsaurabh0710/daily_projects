#!/usr/bin/env python3
"""invisibles - show the characters you cannot see.

Reads files (or stdin) and reports characters that are invisible, deceptive, or
merely whitespace-ish: zero-width joins, bidi overrides, no-break spaces, soft
hyphens, mixed-script words, trailing blanks, stray CRs, byte-order marks.

Exit status is 1 when anything is reported, so it works as a lint step.

    python3 invisibles.py FILE...        # or pipe into it
    python3 invisibles.py --selftest

This source is deliberately pure ASCII -- every non-ASCII character it knows
about is spelled as a codepoint, so the file passes its own check.
"""
import sys
import unicodedata

RISK, NOTE = "risk", "note"

# codepoint, one-cell stand-in, label, severity
_TABLE = [
    (0x200B, "Z", "zero-width space", RISK),
    (0x200C, "Z", "zero-width non-joiner", RISK),
    (0x200D, "Z", "zero-width joiner", RISK),
    (0x2060, "Z", "word joiner", RISK),
    (0xFEFF, "Z", "zero-width no-break space", RISK),
    (0x00AD, "-", "soft hyphen", RISK),
    (0x200E, "B", "left-to-right mark", RISK),
    (0x200F, "B", "right-to-left mark", RISK),
    (0x202A, "B", "LRE bidi embedding", RISK),
    (0x202B, "B", "RLE bidi embedding", RISK),
    (0x202C, "B", "pop directional formatting", RISK),
    (0x202D, "B", "LRO bidi override", RISK),
    (0x202E, "B", "RLO bidi override", RISK),
    (0x2066, "B", "LRI bidi isolate", RISK),
    (0x2067, "B", "RLI bidi isolate", RISK),
    (0x2068, "B", "FSI bidi isolate", RISK),
    (0x2069, "B", "pop directional isolate", RISK),
    (0x00A0, "_", "no-break space", NOTE),
    (0x202F, "_", "narrow no-break space", NOTE),
    (0x2007, "_", "figure space", NOTE),
    (0x2009, "_", "thin space", NOTE),
    (0x3000, "_", "ideographic space", NOTE),
    (0x000B, "v", "vertical tab", NOTE),
    (0x000C, "f", "form feed", NOTE),
]
SPECIAL = {chr(cp): (glyph, label, sev) for cp, glyph, label, sev in _TABLE}

TAB_CELL = chr(0x2192)      # rightwards arrow
CTRL_CELL = chr(0x00B7)     # middle dot
WORD_CHARS = "_$"


def script_of(ch):
    """The first word of a letter's Unicode name is its script: LATIN, CYRILLIC..."""
    try:
        return unicodedata.name(ch).split()[0]
    except ValueError:
        return None


def mixed_script_hits(line):
    """Flag letters from another script sitting inside an otherwise Latin word."""
    hits, i, n = [], 0, len(line)
    while i < n:
        if not (line[i].isalnum() or line[i] in WORD_CHARS):
            i += 1
            continue
        j = i
        while j < n and (line[j].isalnum() or line[j] in WORD_CHARS):
            j += 1
        letters = [(k, line[k]) for k in range(i, j) if line[k].isalpha()]
        scripts = {script_of(c) for _, c in letters} - {None}
        if len(scripts) > 1:
            base = "LATIN" if "LATIN" in scripts else sorted(scripts)[0]
            for k, c in letters:
                sc = script_of(c)
                if sc != base:
                    hits.append((k, "%s letter in a %s word" % (sc.lower(), base.lower()), RISK))
        i = j
    return hits


def scan_line(line):
    hits = [(i, SPECIAL[ch][1], SPECIAL[ch][2]) for i, ch in enumerate(line) if ch in SPECIAL]
    hits += mixed_script_hits(line)
    stripped = line.rstrip(" \t")
    if stripped != line and stripped:
        hits += [(i, "trailing whitespace", NOTE) for i in range(len(stripped), len(line))]
    return sorted(hits)


def render(line, columns):
    """One display cell per source character, so the caret row always lines up."""
    cells = []
    for ch in line:
        if ch == "\t":
            cells.append(TAB_CELL)
        elif ch in SPECIAL:
            cells.append(SPECIAL[ch][0])
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            cells.append(CTRL_CELL)
        else:
            cells.append(ch)
    marks = ["^" if i in columns else " " for i in range(len(line))]
    return "".join(cells), "".join(marks).rstrip()


def check(name, data, out):
    found = 0
    if data.startswith(b"\xef\xbb\xbf"):
        print("%s:1: byte-order mark at start of file" % name, file=out)
        found += 1
        data = data[3:]
    text = data.decode("utf-8", "surrogateescape")
    endings = set()
    for lineno, raw in enumerate(text.splitlines(keepends=True), 1):
        body = raw.rstrip("\r\n")
        endings.add(raw[len(body):])
        if "\r" in body:
            print("%s:%d: carriage return inside the line" % (name, lineno), file=out)
            found += 1
        hits = scan_line(body)
        if not hits:
            continue
        found += len(hits)
        labels = sorted({label for _, label, _ in hits})
        worst = RISK if any(sev == RISK for _, _, sev in hits) else NOTE
        print("%s:%d: [%s] %s" % (name, lineno, worst, ", ".join(labels)), file=out)
        shown, marks = render(body, {i for i, _, _ in hits})
        print("  | %s\n  | %s" % (shown, marks), file=out)
    real = endings - {""}
    if len(real) > 1:
        names = sorted("CRLF" if e == "\r\n" else "LF" if e == "\n" else "CR" for e in real)
        print("%s: mixed line endings (%s)" % (name, " and ".join(names)), file=out)
        found += 1
    if text and not text.endswith(("\n", "\r")):
        print("%s: no newline at end of file" % name, file=out)
        found += 1
    return found


def selftest():
    out = sys.stdout
    sample = (
        "clean line\n"
        "trailing spaces here   \n"
        "nbsp" + chr(0x00A0) + "between words\n"
        "pass" + chr(0x200B) + "word = secret\n"
        "if (" + chr(0x202E) + "access)\n"
        + chr(0x0441) + "onst total = 1\n"
        "no final newline"
    ).encode("utf-8")
    found = check("<sample>", sample, out)
    assert found == 8, found              # 3 trailing blanks + 4 chars + missing newline
    assert scan_line("plain ascii") == []
    assert scan_line("tabs\tare\tfine") == []
    assert [h[1] for h in scan_line("a" + chr(0x200B) + "b")] == ["zero-width space"]
    assert mixed_script_hits(chr(0x0441) + "onst")
    assert not mixed_script_hits("const")
    assert not mixed_script_hits(chr(0x0441) + chr(0x043E) + chr(0x043D))   # all Cyrillic
    shown, marks = render("a\tb" + chr(0x200B) + "c", {3})
    assert shown == "a" + TAB_CELL + "bZc"
    assert marks == "   ^"
    assert check("<clean>", b"fine\n", out) == 0
    assert check("<bom>", b"\xef\xbb\xbfx\n", out) == 1
    print("selftest: ok")


def main(argv):
    if "--selftest" in argv:
        selftest()
        return 0
    total = 0
    if argv:
        for path in argv:
            with open(path, "rb") as fh:
                total += check(path, fh.read(), sys.stdout)
    else:
        total = check("-", sys.stdin.buffer.read(), sys.stdout)
    print("%d finding%s" % (total, "" if total == 1 else "s"), file=sys.stderr)
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
