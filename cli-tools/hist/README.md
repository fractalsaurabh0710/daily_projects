# hist

A terminal histogram. Pipe it anything containing numbers — a log, a column of
measurements, `seq` output — and it scrapes out every number it can find and
draws the distribution.

## Run

```
seq 1 100 | python3 hist.py
python3 hist.py -b 12 -w 50 < data.txt
awk '{print $9}' access.log | python3 hist.py   # response sizes
```

`-b/--bins` sets the bin count, `-w/--width` the widest bar in characters.

Tests: `python3 test_hist.py`

## The interesting bit

Bin count comes from the Freedman–Diaconis rule, `width = 2 * IQR / n^(1/3)`,
rather than from a fixed default. Because the IQR only measures the middle half
of the data, one far-out value widens the plotted range but barely changes the
bin width — so the bulk of the distribution keeps its resolution instead of
collapsing into a single tall bar. Bars are drawn in eighth-blocks (`▏▎▍…█`), so
a bin holding one sample out of ten thousand still renders as a visible sliver
instead of rounding away to nothing.
