# FM-Index

Substring search over the Burrows–Wheeler transform of a string: `count(P)` and
`locate(P)` in time proportional to `|P|`, touching the BWT only — the original
text is never reconstructed to answer a query.

Built from scratch here: suffix array (prefix doubling), BWT, inverse BWT via the
LF mapping, the `C` / `Occ` tables, backward search, and position recovery from a
*sampled* suffix array.

## Run

    python3 main.py

Runs the test suite (including 40 random strings checked against naive
`str` scanning) and then prints a worked example.

## The one interesting bit

`locate()` is why an FM-index is small. Storing the full suffix array would cost
more than the text itself, so only every k-th position is kept. For an unsampled
row, you walk the LF mapping backwards one character at a time — each step moves
to the row for the preceding text position — until you land on a sampled row, then
add the number of steps you took. Same answer, a fraction of the space.

The suffix array here is O(n log²n) rather than linear-time SA-IS; that keeps the
construction to a dozen lines, and it only runs once.
