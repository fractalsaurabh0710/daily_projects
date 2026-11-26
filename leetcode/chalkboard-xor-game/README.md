# Chalkboard XOR Game (LeetCode 810)

Numbers on a chalkboard; players take turns erasing one. If your erasure leaves
the XOR of the rest equal to zero, you lose. If the XOR is *already* zero when
your turn starts, you win. Alice goes first — does she win?

The answer has no search in it:

```python
return xor(nums) == 0 or len(nums) % 2 == 0
```

Run it:

```
python3 main.py
```

## The part worth the write-up

The parity clause looks like a guess. It is forced: erasing `x` is suicide only
when `x == t`, the current XOR, so a player is stuck only when *every* number on
the board equals `t` — and the XOR of an even count of equal values is zero,
which contradicts `t != 0`. An even board with nonzero XOR therefore always has
a safe move, and every safe move hands the opponent an odd board. The parity,
not the values, is what runs out.

A formula cannot test itself, so `main.py` also plays the game out: a memoized
search over every reachable multiset, compared against the one-liner on all 329
multisets drawn from `{0,1,2,3}` with up to 7 numbers. They agree on all 329.
Dropping the parity clause — the rule you write down first — is wrong on 90 of
them, which is exactly the set of even boards with nonzero XOR, and the search
confirms the other side too: Alice loses all 150 odd boards with nonzero XOR.
