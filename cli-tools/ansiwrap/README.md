# ansiwrap

Word-wrap for terminal text that `textwrap` gets wrong: coloured output and
non-Latin scripts.

Three things it handles that counting `len()` does not:

- **Escape sequences are zero columns.** `\x1b[31m` is four characters of
  nothing, so naive wrapping breaks coloured lines short.
- **Characters are not one column wide.** CJK and fullwidth forms take two,
  combining marks take none.
- **A style open at a break is closed and re-opened.** Every output line ends
  reset and begins by restating the live style, so the lines stay independently
  correct when something downstream crops, indents or reorders them.

## Run it

```sh
printf 'The \033[1;31mquick brown\033[0m fox jumps over the lazy dog\n' |
    python3 ansiwrap.py --width 24
cat file.txt | python3 ansiwrap.py          # width from the terminal
python3 ansiwrap.py --selftest              # assertions
```

## The non-obvious part

Styles are tracked as a `{group: code}` snapshot rather than a stack, because
SGR codes replace each other within a group — a second foreground colour
overrides the first, `22` cancels both `1` and `2`. Keeping one code per group
means a re-opened line restates the style in a single short escape instead of
replaying every sequence seen so far. Each line is then rebuilt by exploding it
into `(char, width, style)` cells and emitting an escape only where the style
actually changes, which is also what makes `--width` smaller than a wide
character terminate instead of loop.
