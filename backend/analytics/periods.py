"""SCHEMA §5 period maths, Python only. Pure functions over a date-sorted [(date, adj_close)] series."""
from __future__ import annotations

import bisect
import calendar
from datetime import date, timedelta

Series = list[tuple[date, float]]
RANGE_MONTHS = {"3M": 3, "6M": 6, "1Y": 12, "3Y": 36}  # "ALL" = no lower bound
MAX_BUCKETS = {"M": 12, "Q": 12, "Y": 10}


def months_back(day: date, months: int) -> date:
    """The same day `months` calendar months earlier (negative = later), clamped to the month end."""
    year, month0 = divmod(day.year * 12 + day.month - 1 - months, 12)
    return date(year, month0 + 1, min(day.day, calendar.monthrange(year, month0 + 1)[1]))


def last_on_or_before(series: Series, day: date) -> tuple[date, float] | None:
    """`last(d)`: the last bar on or before `day`."""
    i = bisect.bisect_right(series, day, key=lambda bar: bar[0])
    return series[i - 1] if i else None


def pct(end_value: float, base_value: float) -> float:
    return round((end_value / base_value - 1) * 100, 2)


def change(series: Series, end_day: date, base_day: date) -> dict:
    """§5 change from last(base_day) to last(end_day); null when base_day is before the first bar."""
    end = last_on_or_before(series, end_day)
    base = last_on_or_before(series, base_day) if series and base_day >= series[0][0] else None
    if end is None or base is None:
        return {"pct": None, "base_date": None, "base_value": None,
                "end_value": round(end[1], 2) if end else None}
    return {"pct": pct(end[1], base[1]), "base_date": base[0], "base_value": round(base[1], 2),
            "end_value": round(end[1], 2)}


def ytd_base(as_of: date, basis: str) -> date:
    """Calendar: 31 Dec of the previous year. Fiscal: the last 30 Jun (FY end) before `as_of`."""
    if basis == "fiscal":
        fy_end = date(as_of.year, 6, 30)
        return fy_end if fy_end < as_of else date(as_of.year - 1, 6, 30)
    return date(as_of.year - 1, 12, 31)


def changes(series: Series, as_of: date, basis: str) -> dict[str, dict]:
    """MoM / QoQ / YoY are trailing; only YTD depends on the basis (D-18)."""
    return {"mom": change(series, as_of, months_back(as_of, 1)),
            "qoq": change(series, as_of, months_back(as_of, 3)),
            "ytd": change(series, as_of, ytd_base(as_of, basis)),
            "yoy": change(series, as_of, months_back(as_of, 12))}


def fiscal_year(day: date) -> int:
    """FY label: FY ends 30 Jun, so Jul 2025 – Jun 2026 is FY2026."""
    return day.year + 1 if day.month > 6 else day.year


def bucket(day: date, freq: str, basis: str) -> tuple[str, date, date]:
    """(label, start, end) of the M / Q / Y bucket containing `day` (§5 label table)."""
    if freq == "M":
        return f"{day:%Y-%m}", day.replace(day=1), day.replace(day=calendar.monthrange(day.year, day.month)[1])
    if freq == "Q":  # fiscal quarters share calendar boundaries; only the label differs
        start = date(day.year, (day.month - 1) // 3 * 3 + 1, 1)
        end = months_back(start, -3) - timedelta(days=1)
        if basis == "fiscal":
            return f"FY{fiscal_year(day)} Q{(day.month - 7) % 12 // 3 + 1}", start, end
        return f"{day.year} Q{(day.month - 1) // 3 + 1}", start, end
    if basis == "fiscal":
        fy = fiscal_year(day)
        return f"FY{fy}", date(fy - 1, 7, 1), date(fy, 6, 30)
    return str(day.year), date(day.year, 1, 1), date(day.year, 12, 31)


def returns(series: Series, as_of: date, freq: str, basis: str) -> list[dict]:
    """Up to MAX_BUCKETS[freq] buckets, oldest first; each is last(end) / last(previous end) − 1.
    The bucket that contains `as_of` is `partial`; buckets that end before the first bar are omitted."""
    if not series:
        return []
    spans, day = [], as_of
    while len(spans) < MAX_BUCKETS[freq]:
        label, start, end = bucket(day, freq, basis)
        if end < series[0][0]:
            break
        spans.append((label, start, end))
        day = start - timedelta(days=1)
    out = []
    for label, start, end in reversed(spans):
        moved = change(series, min(end, as_of), start - timedelta(days=1))
        out.append({"label": label, "start": start, "end": end, "pct": moved["pct"],
                    "partial": start <= as_of <= end})
    return out


def window_start(as_of: date, range_: str) -> date | None:
    """Bars strictly after this date are in the range; None for ALL."""
    return months_back(as_of, RANGE_MONTHS[range_]) if range_ in RANGE_MONTHS else None


def rebase(symbol: Series, benchmark: Series, start: date | None) -> list[tuple[date, float, float]]:
    """Both series on their common dates after `start`, rebased to 100 at the first common date."""
    bench = dict(benchmark)
    common = [(d, v, bench[d]) for d, v in symbol if (start is None or d > start) and d in bench]
    if not common:
        return []
    _, s0, b0 = common[0]
    return [(d, round(v / s0 * 100, 2), round(b / b0 * 100, 2)) for d, v, b in common]
