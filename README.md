# daily_projects

A small, self-contained programming project every day. Each one is finished,
runnable, and documented — the goal is a steady habit of building complete little
things rather than accumulating half-started repos.

## Projects

| Date       | Project                                                        | Category  | What it is                                                     |
| ---------- | -------------------------------------------------------------- | --------- | -------------------------------------------------------------- |
| 2026-09-22 | [Unbeatable Tic-Tac-Toe](web-games/tic-tac-toe-minimax/)         | web-games | Minimax with depth-preferred scoring; provably cannot be beaten |

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
