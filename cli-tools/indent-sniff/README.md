# indent-sniff

Guesses the indentation style of a text file -- tabs or spaces, and if spaces,
the unit width -- from the file's content alone.

## Run

    python3 indent-sniff.py FILE [FILE ...]
    python3 indent-sniff.py --selftest

    file                                         style   unit  conf indent depth mixed
    ./algorithms/dancing-links/dlx.py            spaces     4  0.96    138     8     0
    ./web-games/untangle/index.html              spaces     2  1.00    266     7     0

`conf` is the share of indents the chosen unit divides; `mixed` counts lines
that begin with both a tab and a space.

## The interesting part

The obvious statistics both fail. The most common indent width is whatever
nesting level the file spends most of its lines at, not the unit. The most
common *delta* between consecutive lines' indents is polluted by continuation
lines aligned under an open paren, which produce deltas like 13 and -9.

Divisibility is the real signal: every genuine indent is a multiple of the
unit. But a strict GCD is wrong too, and not marginally -- across the 51 source
files in this repo, `gcd` of all space indents gives the right answer 25 times,
while this tool gets 50 (the miss is a file with no indentation at all). One
aligned continuation line at an odd column drops the GCD to 1, which happened
in 13 of those files.

So each candidate unit is scored by the *share* of indents it divides, and the
largest candidate clearing 90% wins. Largest-first is what makes the threshold
work: 2 divides everything 4 divides, so coverage alone always prefers the
smallest unit, and only the ordering recovers the real one. The threshold is
also what buys the noise tolerance a GCD lacks -- a handful of aligned lines
cost a few percent of coverage instead of destroying the answer.
