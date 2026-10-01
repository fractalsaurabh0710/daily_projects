"""Parse a 5-field cron expression and compute when it fires next.

Fields: minute hour day-of-month month day-of-week (0 = Sunday).
Supported syntax per field: *, n, a-b, a-b/s, */s, and comma-separated lists.

The day matching rule is the one real subtlety in cron: if BOTH day-of-month
and day-of-week are restricted (neither is "*"), a date matches when EITHER
one matches -- an OR, not an AND. "0 0 13 * 5" is the 13th of the month *and*
every Friday, not only Friday the 13th.
"""

from datetime import datetime, timedelta

RANGES = [(0, 59), (0, 23), (1, 31), (1, 12), (0, 6)]
NAMES = [
    {},
    {},
    {},
    {m: i + 1 for i, m in enumerate(
        "jan feb mar apr may jun jul aug sep oct nov dec".split())},
    {d: i for i, d in enumerate("sun mon tue wed thu fri sat".split())},
]


def _parse_field(spec, index):
    lo, hi = RANGES[index]
    # Cron lets 7 mean Sunday as well as 0; accept it, normalise below.
    if index == 4:
        hi = 7
    names = NAMES[index]
    values = set()

    for part in spec.split(","):
        step = 1
        if "/" in part:
            part, _, raw_step = part.partition("/")
            step = int(raw_step)
            if step < 1:
                raise ValueError("step must be >= 1: " + spec)

        if part == "*":
            start, end = lo, hi
        elif "-" in part.lstrip("-"):
            a, _, b = part.partition("-")
            start, end = _value(a, names), _value(b, names)
        else:
            start = end = _value(part, names)
            if step != 1:          # "5/15" means 5, 20, 35, 50 -- 5 through hi
                end = hi

        if not (lo <= start <= hi and lo <= end <= hi) or start > end:
            raise ValueError("out of range: %r in field %d" % (part, index))
        values.update(range(start, end + 1, step))

    # Cron accepts 7 for Sunday; normalise it so matching is simple.
    if index == 4 and 7 in values:
        values.discard(7)
        values.add(0)
    return frozenset(values)


def _value(token, names):
    token = token.strip().lower()
    if token in names:
        return names[token]
    return int(token)


class Cron:
    def __init__(self, expression):
        fields = expression.split()
        if len(fields) != 5:
            raise ValueError("expected 5 fields, got %d" % len(fields))
        self.expression = expression
        self.sets = [_parse_field(f, i) for i, f in enumerate(fields)]
        # Remember which day field was wildcarded -- the OR rule needs it.
        self.dom_restricted = fields[2] != "*"
        self.dow_restricted = fields[4] != "*"

    def matches(self, when):
        minute, hour, dom, month, dow = self.sets
        if when.minute not in minute or when.hour not in hour:
            return False
        if when.month not in month:
            return False
        # Python's weekday() is Monday=0; cron wants Sunday=0.
        cron_dow = (when.weekday() + 1) % 7
        dom_ok, dow_ok = when.day in dom, cron_dow in dow
        if self.dom_restricted and self.dow_restricted:
            return dom_ok or dow_ok
        return dom_ok and dow_ok

    def next(self, after=None, limit_days=1500):
        """First matching minute strictly after `after` (default: now)."""
        cursor = (after or datetime.now()).replace(second=0, microsecond=0)
        cursor += timedelta(minutes=1)
        deadline = cursor + timedelta(days=limit_days)
        while cursor < deadline:
            if cursor.day not in self.sets[2] and not (
                    self.dom_restricted and self.dow_restricted):
                # Whole day is impossible -- skip it instead of 1440 ticks.
                cursor = (cursor + timedelta(days=1)).replace(hour=0, minute=0)
                continue
            if self.matches(cursor):
                return cursor
            cursor += timedelta(minutes=1)
        raise ValueError("no match within %d days: %s" % (limit_days, self.expression))

    def upcoming(self, count, after=None):
        out, cursor = [], after or datetime.now()
        for _ in range(count):
            cursor = self.next(cursor)
            out.append(cursor)
        return out


def _test():
    base = datetime(2026, 10, 1, 6, 39)

    assert Cron("* * * * *").next(base) == datetime(2026, 10, 1, 6, 40)
    assert Cron("0 * * * *").next(base) == datetime(2026, 10, 1, 7, 0)
    assert Cron("30 3 * * *").next(base) == datetime(2026, 10, 2, 3, 30)
    assert Cron("*/15 * * * *").upcoming(3, base) == [
        datetime(2026, 10, 1, 6, 45),
        datetime(2026, 10, 1, 7, 0),
        datetime(2026, 10, 1, 7, 15),
    ]
    # Month rollover and a month-restricted expression.
    assert Cron("0 0 1 1 *").next(base) == datetime(2027, 1, 1, 0, 0)
    # Leap-year day: 2028 is the next leap year after 2026.
    assert Cron("0 12 29 2 *").next(base) == datetime(2028, 2, 29, 12, 0)

    # The OR rule: 13th of any month, or any Friday.
    both = Cron("0 0 13 * 5")
    assert both.matches(datetime(2026, 10, 13, 0, 0))   # a Tuesday, but the 13th
    assert both.matches(datetime(2026, 10, 2, 0, 0))    # a Friday, not the 13th
    # With only day-of-week restricted it is a plain AND with "*".
    fridays = Cron("0 0 * * fri")
    assert fridays.next(base) == datetime(2026, 10, 2, 0, 0)
    assert not fridays.matches(datetime(2026, 10, 1, 0, 0))

    # Names, lists, ranges with steps, and 7-as-Sunday.
    assert Cron("0 9 * mar,jun mon-fri").sets[3] == frozenset({3, 6})
    assert Cron("0 0 * * 7").sets[4] == frozenset({0})
    assert Cron("0-30/10 * * * *").sets[0] == frozenset({0, 10, 20, 30})
    assert Cron("5/15 * * * *").sets[0] == frozenset({5, 20, 35, 50})

    for bad in ["* * * *", "60 * * * *", "* * 0 * *", "*/0 * * * *", "30-10 * * * *"]:
        try:
            Cron(bad)
        except ValueError:
            pass
        else:
            raise AssertionError("should have rejected " + repr(bad))

    print("all tests passed")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cron = Cron(" ".join(sys.argv[1:]))
        print(cron.expression)
        for moment in cron.upcoming(5):
            print("  ", moment.strftime("%Y-%m-%d %H:%M  %a"))
    else:
        _test()
