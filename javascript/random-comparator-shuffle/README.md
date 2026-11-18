# Random Comparator Shuffle

`array.sort(() => Math.random() - 0.5)` is the most popular way to shuffle an
array in JavaScript and it is not a shuffle. This measures how badly, and what
the bias is actually made of.

## Run

    node main.js

Everything is driven by a seeded PRNG, so the numbers below reproduce exactly.

## What it does

The test statistic is the position matrix `M[v][p]`: how often value `v` ends up
at position `p` over many trials of shuffling `[0..n-1]`. A uniform shuffle makes
every cell `trials / n`, so the matrix is printed as a percentage of that — 100
everywhere means unbiased. Fisher-Yates is run alongside as the control.

At n=6 over 200,000 trials, Fisher-Yates holds every cell within 1.3% of
expectation (chi2/dof = 1.30). The comparator sort misses by up to 71%, with
chi2/dof = 4194, and the main diagonal — value `v` still sitting at position `v`
— runs 1.40x enriched. The array mostly stays where it was.

## The interesting part

The bias is not noise and not a property of `Math.random`; it is a fingerprint of
the sort algorithm, because an inconsistent comparator makes the output depend
entirely on which comparisons the engine happened to ask for. Two consequences
fall out of the sweep:

- **n=2 is perfectly fair.** One comparison, answered 50/50, two outcomes. The
  idiom is correct for exactly this case.
- **Diagonal enrichment is not monotonic.** It falls from 1.32x at n=4 to 1.06x
  at n=32, then climbs back to 1.16x at n=64 and stays there. Below the
  threshold where V8's TimSort treats the whole array as a single
  binary-insertion run, longer arrays dilute the memory of the input; once
  merging starts, the merge step reintroduces it, because merging two runs
  with a coin-flip comparator keeps re-asking about the same boundary elements.

The comparison count in the last column is the reason the matrix can never be
uniform: a fair shuffle of n items needs log2(n!) bits of entropy, and a sort only
spends about `n log n` comparisons' worth — 5.4 comparisons per element at
n=128 — distributed in a pattern the algorithm chose, not the shuffle.

## Claims

Run directly, the script asserts what it printed: Fisher-Yates uniform to
chi2/dof < 2 with no diagonal memory, and the comparator sort detectably
non-uniform with the diagonal enriched.
