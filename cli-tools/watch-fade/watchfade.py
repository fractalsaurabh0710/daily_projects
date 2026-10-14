#!/usr/bin/env python3
"""watchfade - re-run a command on a timer and highlight what changed.

Like `watch -d`, except a change does not vanish on the next refresh: it is lit
brightly when it appears and then cools over the following few frames, so a
value that moved two seconds ago is still visibly warm. Diffing is done at the
character level inside line-aligned pairs, so a single digit ticking over
highlights one digit rather than the whole row.
"""
import argparse
import subprocess
import sys
import shutil
import time
from difflib import SequenceMatcher

HEAT_MAX = 4  # a change stays visible for this many refreshes
# Styles indexed by (HEAT_MAX - heat): hottest first, coolest last.
HEAT_STYLE = ["\033[30;103m", "\033[30;43m", "\033[33m", "\033[2;33m"]
RESET = "\033[0m"


def char_heat(old, new, heat_old):
    """Heat row for `new`, given the previous text and its (already decayed) heat."""
    heat = [0] * len(new)
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, old, new, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(j2 - j1):
                heat[j1 + k] = heat_old[i1 + k] if i1 + k < len(heat_old) else 0
        elif tag in ("replace", "insert"):
            for j in range(j1, j2):
                heat[j] = HEAT_MAX
    return heat


def decay(row):
    return [max(0, h - 1) for h in row]


def frame_heat(prev_lines, prev_heat, lines):
    """Heat rows for a whole frame: align lines first, then characters within pairs."""
    heat = [None] * len(lines)
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, prev_lines, lines, autojunk=False).get_opcodes():
        if tag == "equal":
            for k in range(j2 - j1):
                heat[j1 + k] = decay(prev_heat[i1 + k])
        elif tag == "replace":
            for k in range(j2 - j1):
                old_i = i1 + k
                if old_i < i2:  # a line paired with an old one: diff the characters
                    heat[j1 + k] = char_heat(prev_lines[old_i], lines[j1 + k],
                                             decay(prev_heat[old_i]))
                else:           # more new lines than old ones: wholly new
                    heat[j1 + k] = [HEAT_MAX] * len(lines[j1 + k])
        elif tag == "insert":
            for j in range(j1, j2):
                heat[j] = [HEAT_MAX] * len(lines[j])
    return [h if h is not None else [0] * len(lines[i]) for i, h in enumerate(heat)]


def render(line, heat, color=True):
    """Wrap each run of equal heat in its style."""
    if not color:
        return line
    out, i = [], 0
    while i < len(line):
        h = heat[i] if i < len(heat) else 0
        j = i
        while j < len(line) and (heat[j] if j < len(heat) else 0) == h:
            j += 1
        chunk = line[i:j]
        out.append(HEAT_STYLE[HEAT_MAX - h] + chunk + RESET if h else chunk)
        i = j
    return "".join(out)


def capture(cmd, width):
    """Run the command once; stdout and stderr merged, tabs expanded, clipped to width."""
    if len(cmd) == 1:
        proc = subprocess.run(cmd[0], shell=True, capture_output=True, text=True)
    else:
        proc = subprocess.run(cmd, capture_output=True, text=True)
    text = proc.stdout + proc.stderr
    return [ln.expandtabs(8)[:width] for ln in text.splitlines()]


def watch(cmd, interval, color):
    prev_lines, prev_heat = [], []
    shown = " ".join(cmd)
    try:
        sys.stdout.write("\033[?25l")  # hide the cursor
        while True:
            cols, _ = shutil.get_terminal_size((80, 24))
            lines = capture(cmd, cols)
            heat = frame_heat(prev_lines, prev_heat, lines)
            body = [render(ln, h, color) for ln, h in zip(lines, heat)]
            header = f"every {interval}s: {shown}"[:cols]
            sys.stdout.write("\033[H\033[K" + header + "\n\033[K\n")
            sys.stdout.write("".join("\033[K" + b + "\n" for b in body))
            sys.stdout.write("\033[J")
            sys.stdout.flush()
            prev_lines, prev_heat = lines, heat
            time.sleep(interval)
    except (KeyboardInterrupt, BrokenPipeError):
        pass
    finally:
        try:
            sys.stdout.write("\033[?25h\n")
            sys.stdout.flush()
        except BrokenPipeError:
            pass


def selftest():
    # One character changes: only that character is hot.
    assert char_heat("abc", "abd", [0, 0, 0]) == [0, 0, HEAT_MAX]
    # Insertion shifts heat along with the characters it belongs to.
    assert char_heat("ac", "abc", [0, 2]) == [0, HEAT_MAX, 2]
    # Heat survives an unchanged frame, one step cooler each time.
    lines, heat = ["cpu 10%"], [[0] * 7]
    heat = frame_heat(lines, heat, ["cpu 11%"])
    assert heat[0] == [0, 0, 0, 0, 0, HEAT_MAX, 0], heat
    for step in range(1, HEAT_MAX + 1):
        heat = frame_heat(["cpu 11%"], heat, ["cpu 11%"])
        assert heat[0][5] == HEAT_MAX - step, (step, heat)
    assert max(heat[0]) == 0  # fully cooled, nothing left lit
    # A brand new line is hot end to end; a surviving one keeps its own heat.
    heat = frame_heat(["keep"], [[0] * 4], ["keep", "fresh"])
    assert heat == [[0, 0, 0, 0], [HEAT_MAX] * 5], heat
    # Lines are matched by content, so an insertion above does not relight the rest.
    heat = frame_heat(["a", "b"], [[0], [0]], ["new", "a", "b"])
    assert heat == [[HEAT_MAX] * 3, [0], [0]], heat
    # Rendering groups equal-heat runs and leaves cold text untouched.
    assert render("abc", [0, 0, 0]) == "abc"
    assert render("ab", [HEAT_MAX, HEAT_MAX]) == HEAT_STYLE[0] + "ab" + RESET
    assert render("ab", [0, 1]) == "a" + HEAT_STYLE[HEAT_MAX - 1] + "b" + RESET
    print("all self-tests passed")


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("-n", "--interval", type=float, default=2.0, help="seconds between runs")
    ap.add_argument("--no-color", action="store_true", help="plain output, no highlighting")
    ap.add_argument("--selftest", action="store_true", help="run the diff/heat tests and exit")
    ap.add_argument("command", nargs="*", help="command to run (quote it to use a shell pipeline)")
    args = ap.parse_args()
    if args.selftest:
        return selftest()
    if not args.command:
        ap.error("a command is required")
    watch(args.command, args.interval, not args.no_color)


if __name__ == "__main__":
    main()
