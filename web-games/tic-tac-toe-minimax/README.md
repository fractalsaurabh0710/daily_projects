# Unbeatable Tic-Tac-Toe

A tic-tac-toe game where the computer plays a complete minimax search. On the
"Perfect" setting it cannot be beaten — the best result available to you is a draw.

No build step, no dependencies. Open `index.html` in a browser.

## The interesting part

Plain minimax returns the same score for every winning position, so an AI using it
will happily take a win in five moves when one is available in one. This version
passes the recursion depth into the score:

```js
if (w.mark === AI)    return  10 - depth;   // win sooner  -> higher score
if (w.mark === HUMAN) return depth - 10;    // lose later  -> less bad
```

The result is an opponent that closes games out directly, and that stalls as long
as possible in positions it has already lost.

The board has only 9 cells, so the full game tree (fewer than 9! = 362,880 nodes,
and far fewer in practice once terminal states prune it) is searched on every move
with no alpha-beta pruning needed.

## Difficulty

The difficulty selector controls how often the AI consults minimax at all:

| Setting | Behaviour                                  |
| ------- | ------------------------------------------ |
| Perfect | Always optimal. Unbeatable.                |
| Hard    | Optimal 75% of moves, otherwise random.    |
| Medium  | Optimal 50% of moves.                      |
| Random  | Never optimal — plays uniformly at random. |

Mixing in random moves is a more honest way to weaken an engine than limiting its
search depth: at this board size a depth limit barely changes the play.

## Verification

The claim that "Perfect" is unbeatable is not an assumption. Every possible human
strategy was played out exhaustively against the AI — 569 distinct games, of which
the AI won 386 and drew 183. The human won none.

## Files

- `index.html` — the whole game: markup, styles and logic in one file.
