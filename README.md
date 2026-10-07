# daily_projects

A small, self-contained programming project every day. Each one is finished,
runnable, and documented — the goal is a steady habit of building complete little
things rather than accumulating half-started repos.

## Projects

| Date       | Project                                                        | Category  | What it is                                                     |
| ---------- | -------------------------------------------------------------- | --------- | -------------------------------------------------------------- |
| 2026-09-22 | [Unbeatable Tic-Tac-Toe](web-games/tic-tac-toe-minimax/)         | web-games | Minimax with depth-preferred scoring; provably cannot be beaten |
| 2026-09-29 | [Bloom Filter](algorithms/bloom-filter/)                         | algorithms | Probabilistic set sized from closed-form formulas; measured 1.09% FP vs 1% designed |
| 2026-10-01 | [Cron Expression Parser](python/cron-next/)                      | python    | Parses 5-field cron expressions and computes the next fire times, OR rule included |
| 2026-10-02 | [Terminal Histogram](cli-tools/hist/)                            | cli-tools | Pipes numbers in and draws their distribution; Freedman–Diaconis binning, eighth-block bars |
| 2026-10-03 | [Reactive Signals](javascript/reactive-signals/)                 | javascript | Fine-grained reactivity in ~120 lines; dependencies tracked automatically, no dep arrays |
| 2026-10-04 | [Longest Substring with K Repeats](leetcode/longest-substring-k-repeating/) | leetcode  | LeetCode 395 two ways: divide-and-conquer on impossible characters, and a window with the distinct count pinned |
| 2026-10-05 | [Gravity Golf](web-games/gravity-golf/)                          | web-games | Three holes of orbital-mechanics golf; velocity Verlet, softened 1/r², every hole proved sinkable |
| 2026-10-06 | [Indexable Skip List](algorithms/indexable-skip-list/)          | algorithms | Sorted multiset with no rotations; spans on every pointer give O(log n) k-th-smallest and rank |
| 2026-10-07 | [Tiny Event Loop](python/tiny-event-loop/)                        | python    | Generators plus a virtual clock: sleep, spawn, join and gather in ~100 lines, no asyncio |

## Categories

Projects are filed by what they are, not by when they were made:

- **`web-games/`** — browser games and interactive toys. Single-file HTML where possible, so they run by double-clicking.
- **`leetcode/`** — algorithm problems, written up with the reasoning and complexity, not just an accepted solution.
- **`python/`** — scripts, small tools, and standard-library explorations.
- **`javascript/`** — Node scripts and language experiments that are not games.
- **`algorithms/`** — classic data structures and algorithms implemented from scratch.
- **`cli-tools/`** — small terminal utilities.

Folders appear as the first project in them is written.

## How to run something

Each project's own README says how, but as a rule:

- `web-games/` — open `index.html` in a browser.
- `python/` — `python3 main.py`, with dependencies noted if there are any.
- `leetcode/` and `algorithms/` — each file runs its own tests when executed directly.

## Conventions

Every project has a README covering what it does, how to run it, and one thing that
was actually interesting about building it. Anything with a correctness claim — a
solver, a game AI, an algorithm — ships with a test that demonstrates the claim
rather than asserting it.
