# Super Washing Machines (LeetCode 517)

`n` washing machines in a row hold some number of dresses each. In one move you
pick any set of machines and each one hands a single dress to a neighbour, all
at the same time. Fewest moves until every machine holds the same amount, or
`-1` if the total does not divide evenly.

## Run

```
python3 solution.py
```

## The answer, and why it is reachable

One pass, no DP:

```python
moves = max(moves, abs(prefix), load - avg)
```

Both terms are lower bounds. `abs(prefix)` is the imbalance that has to cross
the single edge at position `i`, and an edge moves one dress per move.
`load - avg` is the surplus one machine has to emit, and a machine emits one
dress per move. The real content of the problem is that the larger of the two
is also *sufficient* — the constraints never stack up, because a machine can
take a dress from the left and give one to the right within the same move, so
every edge and every machine can run at full rate simultaneously.

That is the part worth testing, and a formula cannot test itself. `brute_force`
does BFS over the actual state space — every subset of machines, each choosing
a side — and the two agree on all 249 balanceable configurations with `n <= 4`
and average `<= 2`.

The `max_prefix_only` function is the version you write if you only read the
problem's examples: it passes all of them and is wrong on 49 of those 249
configurations, the smallest being `[0, 3, 0]`, where the two edges each need
to carry only 1 dress but the middle machine still has to make 2 trips.
