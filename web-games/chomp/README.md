# Chomp

A 5x6 grid of cookies. Eat one and everything below and to the right of it goes
too. The top-left cookie is poisoned, and whoever is forced to eat it loses.
You move first, against an opponent that plays perfectly.

## Run

Open `index.html` in a browser. No build, no dependencies.

## How it works

A position is always a Young diagram, so it is stored as one number per column:
how many cookies remain in it. Eating `(r, c)` is then `heights[i] = min(heights[i], r)`
for every column `i >= c`. Win/loss is a memoized backward induction over those
states &mdash; a position is won if some move leads to a lost one &mdash; which is
cheap because the whole 6x6 box holds only `C(12,6) = 924` diagrams.

## The interesting part

Chomp has a famous one-paragraph proof that the first player wins every rectangle
bigger than 1x1, and the proof hands you no move whatsoever. Suppose the first
player were losing. Then eating just the far corner leaves a position the opponent
wins, so some reply to it wins &mdash; but the first player could have played that
reply as their own opening, since the corner cookie is contained in whatever it
removes. Contradiction. The argument rules out losing without ever naming the move
that avoids it, which is why the AI here has to search.

The page checks the claim rather than quoting it: on load it solves every rectangle
inside 6x6 and reports whether each one's value matches, 1x1 being the sole loss.
A pleasant side-effect of the search: on square boards the winning opening is always
`(1, 1)`, leaving an L of two arms, after which perfect play is just keeping the arms
equal &mdash; verified for 2x2 through 7x7 in the tests. No such rule exists for
non-square boards, and none is known.

## Tests

The game-theory half of the script is pure and has no DOM dependency, so it can be
extracted and exercised directly:

    node chomp_test.js index.html

checking the move rule, the three small hand-known values (`1x1` lost, `2x1` lost,
`2x2` won), the square-board diagonal, and the full 6x6 sweep.
