# dupe-sieve

Finds duplicate files while reading as little of them as possible, and tells you
how little that was.

```
python3 dupes.py ~/Downloads ~/Desktop
python3 dupes.py . --min-size 4096
python3 dupes.py --selftest
```

Output is one block per group of identical files, largest reclaimable first,
then a summary:

```
1.4 MiB x3
    ./photos/IMG_0041.jpg
    ./photos/old/IMG_0041.jpg
    ./backup/IMG_0041.jpg

194 files, 391.5 KiB on disk
1 duplicate group, 225 B reclaimable
read 7.9 KiB to find them (2.0% of the data)
```

Nothing is deleted or moved — it only reports.

## The interesting part

Hashing every file to find duplicates reads every byte on disk, which is the
whole cost of the job. Almost none of that reading is necessary: a file whose
size is unique cannot have a duplicate, and `stat` already knows the size.

So the files pass through three sieves, cheapest first — size, then a hash of
the first 4 KiB, then the whole file — and a file only reaches a stage if
something else is still tied with it. Files with a unique size are read zero
times. Files that share a size but differ early are read 4 KiB and dropped.
Only the near-certain duplicates are read in full, and those are exactly the
files you wanted to find. The last summary line is the accounting: on a typical
tree it reads a few percent of the data.

Two details the middle sieve needs. A file of 4 KiB or less *is* its own head,
so hashing it twice would double the read for small files — those skip straight
to the full stage. And the head hash is only meaningful alongside the size, so
groups are keyed on `(size, head)` rather than the hash alone.

Hard links and overlapping roots are deduplicated by `(st_dev, st_ino)` before
any hashing, so the same file reached twice is one file and never reports as a
duplicate of itself.

`--selftest` builds a temp tree containing a true duplicate, a file with the
same size and head but a different final byte, a same-size file differing
immediately, and a duplicate pair shorter than the head window — then asserts
both the groups found and the exact byte count read.
