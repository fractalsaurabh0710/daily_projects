# watchfade

`watch -d` with a memory. Re-runs a command on a timer and highlights what
changed — but instead of the highlight disappearing on the next refresh, it
cools over the following four frames: bright yellow block when it first moves,
then dimmer, then faint, then gone. A glance at the screen tells you not just
what changed but roughly how long ago.

## Run it

```sh
python3 watchfade.py -n 1 'date +%T; uptime'
python3 watchfade.py --selftest     # diff and heat-decay tests
```

Options: `-n/--interval` seconds between runs (default 2), `--no-color` for
plain output. A single quoted argument is run through the shell, so pipelines
work; multiple arguments are exec'd directly without one.

## The interesting part

Diffing is two-level. Lines are aligned first with `SequenceMatcher`, then
characters are diffed only *within* each matched pair of lines — so a ticking
clock lights up the one digit that moved, not the whole row. Each line carries a
per-character array of heat values, and on an `equal` opcode that array is
carried across to the new frame and decremented. Because alignment is by
content, inserting a line at the top shifts everything down without relighting
any of it: the heat follows the text it belongs to rather than the screen row it
happened to be on.
