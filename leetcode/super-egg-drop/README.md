# Super Egg Drop (LeetCode 887)

`k` eggs, `n` floors, an unknown floor above which eggs break. Find the
worst-case number of drops needed to locate it exactly.

## Run

    python3 super_egg_drop.py

Runs the tests, then prints the coverage table and the drop counts for
`n = 10000`.

## The inversion

The natural DP is over the state — eggs left and floors still in play — and it
is a minimum over a maximum:

    dp[k][n] = 1 + min over x of max(dp[k-1][x-1], dp[k][n-x])

That is `O(k*n^2)`, which dies at `n = 10000`. Turning the question around
removes both the min and the max. Let `f(k, m)` be the number of floors `k`
eggs can clear in `m` drops. The first drop breaks or it doesn't, so

    f(k, m) = f(k-1, m-1) + f(k, m-1) + 1

and the answer is the smallest `m` with `f(k, m) >= n`. Nothing is being
*chosen* here: an optimal strategy can always place its first drop exactly
where the two branches balance, so the split that the forward DP searches for
is just the sum of the two subproblems.

That recurrence is Pascal's rule, so `f(k, m) = C(m,1) + ... + C(m,k)`, which
collapses to `2^m - 1` once `k >= m` — unlimited eggs is binary search, which
is the sanity check the whole derivation has to pass.

## What is verified

- Known answers: `(2, 6) -> 3`, `(3, 14) -> 4`, `(2, 100) -> 14`, `(2, 1000) -> 45`.
- The slow state DP, the inverted DP and the binomial closed form agree on every
  `k` in 1..6 and `n` in 1..80.
- `f(k, m)` from the recurrence equals the binomial sum for all `k <= 8`, `m <= 14`.
- `f(m, m) == 2^m - 1`, and `drops(m, 2^m - 1) == m` — enough eggs really is
  binary search.

## One number worth noticing

Two eggs and 10000 floors need 141 drops; three eggs need 40, and eight need 14.
The third egg is worth more than the first hundred floors of patience — coverage
grows like `m^k / k!`, so each extra egg raises the degree of the polynomial
rather than its constant.
