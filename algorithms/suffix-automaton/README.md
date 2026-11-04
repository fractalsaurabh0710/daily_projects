# Suffix Automaton

The smallest deterministic automaton that accepts exactly the suffixes of a
string, built online in O(n) for a fixed alphabet — one character at a time, with
no rebuild when the next one arrives.

```
python3 suffix_automaton.py
```

Running the file checks every claim against brute force on random strings, then
prints a summary for `mississippi`.

## What it answers

- `"iss" in sam` — is this a substring?
- `sam.occurrences("iss")` — how many times does it occur?
- `sam.distinct_substrings()` — how many distinct substrings does the text have?
- `sam.longest_common_substring(other)` — longest substring shared with another string.

## The interesting part

Each state is an equivalence class of substrings that end at exactly the same set
of positions, and that one idea is what makes the automaton answer so many
different questions. Occurrence counting needs no extra structure: a state's count
is the sum of its children's counts in the suffix-link tree, so one pass over the
states sorted by length fills in every answer. Distinct substrings fall out the
same way — each state contributes `length[v] - length[link[v]]` substrings, the
span of lengths it is the longest representative for, and summing that over all
states gives 53 for `mississippi` out of 66 start/end position pairs.

The construction's hard case is the clone: when extending by a character that
already has a transition, the state it leads to may represent substrings that are
*not* all suffixes of the new text. It gets split into a clone carrying the short
half, and the transitions pointing at it are rewired. That branch is why the state
count is bounded by 2n-1 rather than n.
