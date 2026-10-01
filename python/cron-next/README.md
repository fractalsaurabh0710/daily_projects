# cron-next

A cron expression parser that answers the only question you ever actually have
about one: *when does this next fire?* Standard library only.

Handles the 5 classic fields (`minute hour day-of-month month day-of-week`) with
`*`, numbers, lists, ranges, steps (`*/15`, `0-30/10`, `5/15`), and three-letter
month and day names (`mar`, `mon-fri`).

## Run

    python3 cron_next.py                          # runs the assert suite
    python3 cron_next.py "*/20 9-17 * * mon-fri"  # prints the next 5 fire times

## The interesting part

If **both** day-of-month and day-of-week are restricted, cron ORs them instead of
ANDing them. `0 0 13 * fri` fires every Friday *and* on the 13th of every month —
not on Friday the 13th. If either field is `*`, it goes back to a plain AND. Almost
every hand-rolled cron parser gets this backwards, so the test suite pins it down
with both a Tuesday-the-13th and a plain-Friday case.

The search is a minute-by-minute walk forward, but it skips an entire day at a
time when the day-of-month can't match, which is what keeps `0 12 29 2 *`
(Feb 29) from ticking through two years of minutes to reach 2028.
