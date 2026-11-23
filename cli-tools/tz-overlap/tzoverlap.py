#!/usr/bin/env python3
"""tzoverlap - the working hours a set of time zones actually share.

    tzoverlap America/New_York Asia/Kolkata:10-19 Europe/London

Each argument is a zone, optionally with its own working window as
START-END in 24h local time (default 09-17). A window whose end is at or
before its start wraps past midnight, so `Asia/Tokyo:22-6` is a night shift.

The overlap is computed on the UTC timeline and only then rendered in the
first zone's local time, which is the only way to get it right: zones are
not whole hours apart, days are not 24 hours long, and the shared window
moves whenever any one of the zones changes its offset.
"""

import sys
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

SLOT = 30                 # minutes per rendered cell
SCAN_DAYS = 120           # how far ahead to look for a shift


def parse_spec(spec):
    name, _, hours = spec.partition(":")
    start, end = 9, 17
    if hours:
        a, _, b = hours.partition("-")
        start, end = int(a), int(b)
        if not (0 <= start <= 23 and 0 <= end <= 24):
            raise ValueError("hours out of range in %r" % spec)
    return name, ZoneInfo(name), start, end


def working(local, start, end):
    """Is this local time inside [start, end)? Wraps when end <= start."""
    m = local.hour * 60 + local.minute
    s, e = start * 60, end * 60
    return s <= m < e if s < e else (m >= s or m < e)


def day_bounds(d, tz):
    """UTC instants of local midnight and the next local midnight.

    Not 24h apart on a DST day -- that is the point of asking the zone.
    """
    nxt = d + timedelta(days=1)
    a = datetime(d.year, d.month, d.day, tzinfo=tz)
    b = datetime(nxt.year, nxt.month, nxt.day, tzinfo=tz)
    return a.astimezone(timezone.utc), b.astimezone(timezone.utc)


def slots(d, zones):
    """One midpoint instant per cell, plus a per-zone working flag."""
    lo, hi = day_bounds(d, zones[0][1])
    out, t = [], lo
    step = timedelta(minutes=SLOT)
    while t < hi:
        mid = t + step / 2
        flags = [working(mid.astimezone(tz), s, e) for _, tz, s, e in zones]
        out.append((t, mid, flags))
        t += step
    return out


def runs(cells):
    """Contiguous stretches where every zone is working, as (start, end) UTC."""
    spans, open_at = [], None
    for t, _, flags in cells:
        if all(flags):
            if open_at is None:
                open_at = t
        elif open_at is not None:
            spans.append((open_at, t))
            open_at = None
    if open_at is not None:
        spans.append((open_at, cells[-1][0] + timedelta(minutes=SLOT)))
    return spans


def hhmm(t, tz):
    return t.astimezone(tz).strftime("%H:%M")


def signature(d, zones):
    """What the shared window looks like, as text, in the first zone."""
    ref = zones[0][1]
    return tuple((hhmm(a, ref), hhmm(b, ref)) for a, b in runs(slots(d, zones)))


def render(d, zones):
    cells = slots(d, zones)
    ref_name, ref, _, _ = zones[0]
    width = max(len(n) for n, _, _, _ in zones) + 2

    ruler = [" "] * len(cells)
    for i, (t, _, _) in enumerate(cells):
        local = t.astimezone(ref)
        if local.minute == 0 and local.hour % 3 == 0:
            for j, ch in enumerate(str(local.hour)):
                if i + j < len(ruler):
                    ruler[i + j] = ch
    print(" " * width + "".join(ruler) + "   (%s local)" % ref_name)

    for idx, (name, tz, s, e) in enumerate(zones):
        bar = "".join("#" if c[2][idx] else "." for c in cells)
        off = cells[0][1].astimezone(tz).utcoffset().total_seconds() / 3600
        print("%-*s%s  %02d-%02d  UTC%+g" % (width, name, bar, s, e, off))

    shared = runs(cells)
    bar = "".join("=" if all(c[2]) else " " for c in cells)
    print("%-*s%s" % (width, "overlap", bar))
    if not shared:
        print("\n  no shared working hours on %s" % d)
        return
    total = sum((b - a).total_seconds() for a, b in shared) / 3600
    for a, b in shared:
        print("\n  %s - %s  %s   (%.1fh)" % (hhmm(a, ref), hhmm(b, ref), ref_name, (b - a).total_seconds() / 3600))
        for name, tz, _, _ in zones[1:]:
            print("  %s - %s  %s" % (hhmm(a, tz), hhmm(b, tz), name))
    if len(shared) > 1:
        print("\n  %.1fh shared in total" % total)


def scan(d, zones):
    """Report the next date the shared window is not what it is today."""
    base = signature(d, zones)
    for n in range(1, SCAN_DAYS + 1):
        nxt = d + timedelta(days=n)
        sig = signature(nxt, zones)
        if sig != base:
            shown = ", ".join("%s-%s" % p for p in sig) or "nothing"
            print("\n  shifts on %s (in %d days): %s" % (nxt, n, shown))
            return
    print("\n  stable for the next %d days" % SCAN_DAYS)


def main(argv):
    if len(argv) < 2:
        print(__doc__.strip())
        return 2
    args = [a for a in argv[1:] if not a.startswith("--on=")]
    on = [a[5:] for a in argv[1:] if a.startswith("--on=")]
    d = date.fromisoformat(on[0]) if on else date.today()
    try:
        zones = [parse_spec(a) for a in args]
    except ZoneInfoNotFoundError as exc:
        print("unknown time zone: %s" % exc, file=sys.stderr)
        return 1
    if len(zones) < 2:
        print("need at least two zones", file=sys.stderr)
        return 1
    print("%s  %s\n" % (d, d.strftime("%A")))
    render(d, zones)
    scan(d, zones)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
