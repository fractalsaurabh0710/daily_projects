# tzoverlap

The working hours a set of time zones actually share, drawn as a band.

```
python3 tzoverlap.py America/New_York Asia/Kolkata:10-19 Europe/London
python3 tzoverlap.py Europe/London Asia/Kolkata --on=2027-03-14
```

Each argument is an IANA zone, optionally with its own window as `START-END`
in 24h local time (default `09-17`). A window whose end is at or before its
start wraps past midnight, so `Asia/Tokyo:22-6` is a night shift. Two zones
minimum; the first one is the zone everything is reported in. Standard
library only.

## The part worth knowing

Everything is decided on the UTC timeline and only translated into local time
to be printed. Reasoning in local hours looks fine and quietly breaks three
ways: Kolkata is `UTC+5.5`, so no arithmetic in whole hours lands on its
boundaries; a local day is not 24 hours long, and the clock-change days in
this repo's own tests come out as 46 and 50 half-hour cells rather than 48;
and each zone changes offset on its own date, so a shared window is a fact
about a particular day rather than about the zones.

That last one is why the tool scans forward for the next day the window
changes. The example in the first line above is the case: New York, Kolkata
and London have **no** overlapping working hours at all through the winter,
and get exactly 30 minutes of one on 2027-03-14 — not because anyone's
working hours changed, but because US daylight saving starts eleven days
before Europe's and briefly narrows the gap.
