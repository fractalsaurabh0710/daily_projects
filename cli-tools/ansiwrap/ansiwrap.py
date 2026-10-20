#!/usr/bin/env python3
"""ansiwrap - word-wrap terminal text without breaking colour or wide characters.

    ansiwrap.py [--width N] [FILE ...]      # wrap stdin or files to stdout
    ansiwrap.py --selftest                  # run the assertions

Unlike textwrap, escape sequences count as zero columns, CJK characters count
as two, and a style that is open at a line break is closed and re-opened on the
next line so each output line is independently colourable.
"""
import re
import shutil
import sys
import unicodedata

SGR_RE = re.compile(r"\x1b\[([0-9;]*)m")

# Re-opening a style after a break needs one code per group, not the whole
# history: a second foreground colour replaces the first rather than stacking.
_GROUPS = {1: "weight", 2: "weight", 22: "weight", 3: "italic", 23: "italic",
           4: "under", 24: "under", 5: "blink", 6: "blink", 25: "blink",
           7: "invert", 27: "invert", 8: "hide", 28: "hide",
           9: "strike", 29: "strike"}
_RESETS = {22, 23, 24, 25, 27, 28, 29, 39, 49}


def _group(code):
    if code in _GROUPS:
        return _GROUPS[code]
    if 30 <= code <= 39 or 90 <= code <= 97:
        return "fg"
    if 40 <= code <= 49 or 100 <= code <= 107:
        return "bg"
    return None


def apply_sgr(state, params):
    """Fold one SGR sequence into a {group: codes} snapshot of the live style."""
    state = dict(state)
    codes = [int(p) for p in params.split(";") if p != ""] or [0]
    i = 0
    while i < len(codes):
        code = codes[i]
        if code == 0:
            state.clear()
        elif code in (38, 48):
            # 38;5;N (256 colour) or 38;2;R;G;B (truecolour)
            width = 3 if i + 1 < len(codes) and codes[i + 1] == 5 else 5
            span = codes[i:i + width]
            state["fg" if code == 38 else "bg"] = ";".join(map(str, span))
            i += len(span) - 1
        elif code in _RESETS:
            state.pop(_group(code), None)
        else:
            group = _group(code)
            if group:
                state[group] = str(code)
        i += 1
    return state


def char_width(ch):
    """Columns a character occupies in a terminal."""
    if unicodedata.combining(ch) or unicodedata.category(ch) in ("Mn", "Me", "Cf"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def display_width(text):
    return sum(char_width(c) for c in SGR_RE.sub("", text))


def _cells(line):
    """Explode a line into (char, width, style) triples, escapes absorbed."""
    out, state, i = [], {}, 0
    while i < len(line):
        match = SGR_RE.match(line, i)
        if match:
            state = apply_sgr(state, match.group(1))
            i = match.end()
            continue
        out.append((line[i], char_width(line[i]), state))
        i += 1
    return out


def _render(cells):
    """Rebuild text from cells, emitting the minimum escapes to track style."""
    parts, cur = [], {}
    for ch, _w, state in cells:
        if state != cur:
            parts.append("\x1b[0m")
            if state:
                parts.append("\x1b[" + ";".join(state.values()) + "m")
            cur = state
        parts.append(ch)
    if cur:
        parts.append("\x1b[0m")
    return "".join(parts)


def wrap_line(line, width):
    runs = []
    for cell in _cells(line):
        space = cell[0].isspace()
        if runs and runs[-1][0] == space:
            runs[-1][1].append(cell)
        else:
            runs.append((space, [cell]))

    out, cur, curw = [], [], 0
    for index, (space, run) in enumerate(runs):
        run = list(run)
        if space:
            if cur or index == 0:          # keep the original indent
                cur.extend(run)
                curw += sum(c[1] for c in run)
            continue
        runw = sum(c[1] for c in run)
        while runw > width:               # a single word wider than the line
            if cur:
                out.append(_render(cur))
                cur, curw = [], 0
            take, takew = [], 0
            while run and takew + run[0][1] <= width:
                take.append(run.pop(0))
                takew += take[-1][1]
            if not take:
                break                     # width smaller than one character
            out.append(_render(take))
            runw = sum(c[1] for c in run)
        if cur and curw + runw > width:
            while cur and cur[-1][0].isspace():
                cur.pop()
            out.append(_render(cur))
            cur, curw = [], 0
        cur.extend(run)
        curw += runw
    if cur or not out:
        out.append(_render(cur))
    return out


def wrap(text, width):
    lines = []
    for line in text.split("\n"):
        lines.extend(wrap_line(line, width))
    return "\n".join(lines)


def selftest():
    plain = lambda s: SGR_RE.sub("", s)

    got = wrap("the quick brown fox jumps over it", 10).split("\n")
    assert all(display_width(l) <= 10 for l in got), got
    assert " ".join(plain(l).strip() for l in got) == "the quick brown fox jumps over it"

    got = wrap("\x1b[31mred text wraps here\x1b[0m", 8).split("\n")
    assert all(l.endswith("\x1b[0m") for l in got), got
    assert all("31" in l for l in got), got
    assert all(display_width(l) <= 8 for l in got), got

    got = wrap("\x1b[1mbold \x1b[31mand red words\x1b[0m", 9).split("\n")
    assert "1" in got[-1].split("m")[0] or "1;" in got[-1], got
    assert "31" in got[-1], got           # both open styles survive the break

    got = wrap("日本語テキスト", 6).split("\n")
    assert [plain(l) for l in got] == ["日本語", "テキス", "ト"], got

    assert display_width("éclair") == 6          # combining acute is free
    assert display_width("\x1b[38;5;208mx\x1b[0m") == 1

    got = wrap("\x1b[38;5;208mlongorangeword\x1b[0m", 6).split("\n")
    assert len(got) == 3 and all("38;5;208" in l for l in got), got

    assert wrap("    indented text here", 12).split("\n")[0].startswith("    ")
    assert wrap("", 10) == ""
    print("ansiwrap: all tests passed")


def main(argv):
    if "--selftest" in argv:
        return selftest()
    width = shutil.get_terminal_size((80, 24)).columns
    files = []
    i = 0
    while i < len(argv):
        if argv[i] in ("-w", "--width"):
            i += 1
            width = int(argv[i])
        else:
            files.append(argv[i])
        i += 1
    if files:
        text = "".join(open(f, encoding="utf-8").read() for f in files)
    else:
        text = sys.stdin.read()
    trailing = text.endswith("\n")
    sys.stdout.write(wrap(text.rstrip("\n"), width) + ("\n" if trailing else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
