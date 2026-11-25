# Mastermind — Knuth's Five-Guess Algorithm

Four pegs, six colours, repeats allowed: 1296 possible codes. Donald Knuth showed in
1977 that five guesses always suffice, and that the strategy achieving it is
*minimax* — at each turn play the guess whose worst-case partition of the remaining
candidates is smallest, even when that guess cannot possibly be the answer.

Open `index.html` in a browser. Play normally with the colour swatches; after each
guess the board shows how many candidates survived, and the panel underneath shows
what the minimax solver would have played instead and the worst case that guess
guarantees. "Prove it" then self-plays all 1296 secrets and reports the distribution.

    worst case: 5 guesses
    mean: 4.4761
      1 guesses: 1      2 guesses: 6      3 guesses: 62
      4 guesses: 533    5 guesses: 694
    strategy-tree nodes visited: 1379     ~100 ms

The counterintuitive part is that the solver often guesses a code it has already
ruled out. Maximising the chance of being right this turn and minimising the
candidates left next turn are different objectives, and the second one wins: a code
known to be wrong can still split the survivors more evenly than any live candidate.

Two things make the full 1296-secret proof run in a tenth of a second rather than
minutes. The feedback function is precomputed once into a 1296x1296 `Uint8Array`, so
scoring a guess against a candidate is an array index. And because the solver is
deterministic, the strategy is a *tree*: every distinct path of (guess, answer) pairs
is visited once and cached, so 1296 playthroughs only ever evaluate 1379 decisions.

That cache key has to include the guess, not just the answer. The first version keyed
on answers alone, which is sound when only the solver plays — but a human guess that
draws the same ●○ pattern leaves a different candidate set behind, and the poisoned
entry moved the measured mean off Knuth's 4.4761 by eight ten-thousandths.
