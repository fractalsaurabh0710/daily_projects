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
| 2026-10-08 | [Disk Usage Treemap](cli-tools/du-treemap/)                       | cli-tools | Squarified treemap of directory sizes in coloured terminal blocks; half-cell units fix the aspect ratio |
| 2026-10-09 | [Mini Spreadsheet](javascript/mini-spreadsheet/)                   | javascript | Formula parser plus a dependency graph discovered during evaluation; only downstream cells recompute |
| 2026-10-10 | [Shortest Subarray with Sum at Least K](leetcode/shortest-subarray-sum-at-least-k/) | leetcode  | LeetCode 862 with negatives allowed: prefix sums plus a monotonic deque, where the sliding window has nothing to slide against |
| 2026-10-11 | [Laser Mirrors](web-games/laser-mirrors/)                         | web-games | Rotate-only mirror puzzle; the generator walks the beam to lay out a solution, then flips mirrors so every puzzle is solvable by construction |
| 2026-10-12 | [FM-Index](algorithms/fm-index/)                                 | algorithms | Substring search straight off the Burrows-Wheeler transform; a sampled suffix array walks LF backwards to recover positions |
| 2026-10-13 | [Call-Tree Profiler](python/call-tree-profiler/) | python | Deterministic profiler on sys.setprofile that keeps the call shape instead of a flat table; C-level calls get their own nodes |
| 2026-10-14 | [watchfade](cli-tools/watch-fade/) | cli-tools | `watch -d` whose highlights cool over four refreshes instead of vanishing; line-aligned, then character-level, so one ticking digit lights alone |
| 2026-10-15 | [Copy-on-Write Drafts](javascript/copy-on-write-drafts/) | javascript | Mutate a draft freely and get an immutable copy that shares every untouched subtree; a Proxy copies the spine on first write, not the leaves |
| 2026-10-16 | [Subarrays with K Different Integers](leetcode/subarrays-with-k-distinct/) | leetcode  | LeetCode 992 two ways: exactly(k) as atMost(k) minus atMost(k-1), and a single pass carrying two left edges whose gap is the count |
| 2026-10-17 | [Untangle](web-games/untangle/) | web-games | Planarity puzzle whose generator builds a crossing-free drawing first, then scrambles it, so every board is solvable by construction |
| 2026-10-18 | [Dancing Links](algorithms/dancing-links/) | algorithms | Algorithm X over a self-unlinking mesh of doubly linked nodes; optional columns turn N-queens, which is not an exact cover, into one |
| 2026-10-19 | [AST Semantic Diff](python/ast-semantic-diff/) | python | Diffs two Python files through their syntax trees, so reformatting, comments, reworded docstrings and renamed locals each report as what they are rather than as changed code |
| 2026-10-20 | [ansiwrap](cli-tools/ansiwrap/) | cli-tools | Word-wraps coloured terminal text: escapes count as zero columns, CJK as two, and a style open at the break is closed and re-opened so every line stands alone |
| 2026-10-21 | [Streaming JSON Select](javascript/streaming-json-select/) | javascript | Feed JSON in chunks of any size and get back only the values matching a path pattern; the parse state lives in fields rather than on the call stack, so a chunk may split mid-string or mid-escape |
| 2026-10-22 | [Burst Balloons](leetcode/burst-balloons/) | leetcode  | LeetCode 312 by deciding which balloon bursts *last*: choosing the first one leaves the two halves entangled, choosing the last one makes its neighbours known and the sides independent |
| 2026-10-23 | [Tilt Maze](web-games/tilt-maze/) | web-games | Slide-until-you-hit-something puzzle; the ball can only rest where a wall stops it, so the generator takes the goal from a BFS over resting places and par is the true shortest solution |
| 2026-10-24 | [Aho-Corasick](algorithms/aho-corasick/) | algorithms | Every pattern found in one pass: the BFS that computes failure links also fills in every missing trie edge, so matching never steps backwards, and a second chain of links reports the patterns hiding as suffixes of the one just matched |
| 2026-10-25 | [Exact Floats](python/exact-floats/) | python | The full decimal value of a float, with no rounding anywhere: a float is n/2**k, so multiplying by 5**k turns the denominator into a decimal point — 0.1 takes 55 digits to write down exactly, and the smallest subnormal takes 751 |
| 2026-10-26 | [dupe-sieve](cli-tools/dupe-sieve/) | cli-tools | Duplicate finder that barely reads anything: size, then a 4 KiB head hash, then the whole file, so only near-certain duplicates are ever read through — and it prints what fraction of the data that was |
| 2026-10-27 | [Promises from Scratch](javascript/promises-from-scratch/) | javascript | A Promise built on queueMicrotask that matches the native one tick for tick; the test runs the same program under both and the logs come out line-for-line identical, adoption's two-tick penalty included |
| 2026-10-28 | [Russian Doll Envelopes](leetcode/russian-doll-envelopes/) | leetcode  | LeetCode 354 as longest increasing subsequence over heights, which only works once ties in width sort by height *descending* — that one minus sign makes a tied group unusable by an increasing run, so the ordering enforces the constraint the LIS pass cannot see |
| 2026-10-29 | [Zip Grid](web-games/zip-grid/) | web-games | Draw one line through every cell, hitting the numbers in order; rather than searching for a Hamiltonian path the generator backbites a boustrophedon snake into a random one and numbers cells along it, so the solution exists before the puzzle does |
| 2026-10-30 | [Suffix Automaton](algorithms/suffix-automaton/) | algorithms | The smallest DFA accepting exactly the suffixes of a string, built online one character at a time; every state is a set of substrings sharing their end positions, so one pass over the suffix-link tree answers occurrence counts, and `length[v] - length[link[v]]` summed over states counts the 53 distinct substrings of `mississippi` |
| 2026-11-02 | [Basmati Grain Profiler](food-tech/basmati-grain-profiler/) | food-tech | Part 1 of 7: PNG reader/writer on zlib and a synthetic rice-on-a-mat generator with exact ground truth, so each later measurement stage can be tested against known lengths, breadths and chalk fractions |
| 2026-11-03 | [Splay Tree](algorithms/splay-tree/) | algorithms | A BST that stores no balance information at all: 7.16 probes/access on a skewed workload where a perfectly balanced tree pays 10.00, and an in-order scan of a 1..n path stays at 5.32 probes while log n climbs from 11 to 15 |
| 2026-11-04 | [Dict Collisions](python/dict-collisions/) | python | CPython's dict insertion path in pure Python, predicting a real dict's `__eq__` calls to the comparison; whether n colliding keys cost n(n-1)/2 depends on the hash *value*, since `perturb` dies before the first step for anything below 32 and leaves a permutation that cannot revisit a slot |
| 2026-11-05 | [invisibles](cli-tools/invisibles/) | cli-tools | Lints the characters you cannot see -- zero-width joins, bidi overrides, mixed-script words -- and aligns its caret row by rendering every source character to exactly one display cell, so tabs and zero-width characters stop breaking the columns |
| 2026-11-06 | [Algebraic Effects](javascript/algebraic-effects/) | javascript | Generators as resumable computations: a program yields what it wants and a stack of handlers decides how, so the same untouched logic runs under a lookup table or an async fetcher with identical output -- and a handler can answer a failure with a substitute value, resuming the loop at the expression that asked instead of unwinding to a catch |
| 2026-11-07 | [Lights Out](web-games/lights-out/) | web-games | The 5x5 board as a linear system over GF(2): the press matrix is singular with a 2-dimensional null space, so every solvable board has exactly four solutions and the fewest-press one falls out of comparing them -- and since only one board in four is reachable, the generator presses its way out of a cleared board rather than lighting cells at random |

## Categories

Projects are filed by what they are, not by when they were made:

- **`web-games/`** — browser games and interactive toys. Single-file HTML where possible, so they run by double-clicking.
- **`leetcode/`** — algorithm problems, written up with the reasoning and complexity, not just an accepted solution.
- **`python/`** — scripts, small tools, and standard-library explorations.
- **`javascript/`** — Node scripts and language experiments that are not games.
- **`algorithms/`** — classic data structures and algorithms implemented from scratch.
- **`cli-tools/`** — small terminal utilities.
- **`food-tech/`** — food-industry quality-control tools, built as multi-day projects: grading, contamination and spoilage detection.

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
