# du-treemap

Disk usage as a squarified treemap, drawn with coloured blocks in the terminal.
Each rectangle's **area** is proportional to the bytes under that child, so the
thing eating the directory is the thing that takes up the most screen.

```
python3 du_treemap.py [path] [--top N] [--width COLS] [--height ROWS]
python3 du_treemap.py --selftest
```

Defaults: current directory, 14 largest children (the rest collapse into a
`+N more` tile), 78x20 characters. Python 3 standard library only; symlinks are
never followed.

The layout is the squarified algorithm of Bruls, Huizing & van Wijk (2000):
walk the children largest-first and keep adding to the current row while doing
so improves its worst aspect ratio, then start a fresh row in the leftover
rectangle.

The non-obvious part is that a terminal cell is roughly twice as tall as it is
wide, so laying out in cell coordinates makes every "square" come out as a
letterbox. `render` works in half-cell-wide units and stretches x by two on the
way out.

`--selftest` checks the layout rather than asserting it: over 200 random inputs
every rectangle's area matches its requested share, all of them stay inside the
bounding box, and no two of them overlap.
