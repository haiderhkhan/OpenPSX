"""P2-06: SCHEMA §5 period maths on small synthetic series (no DB)."""
from __future__ import annotations

from datetime import date, timedelta

import pytest

from backend.analytics import periods


def weekday_series(start: date, end: date, step: float = 1.0) -> periods.Series:
    """Value grows by `step` per weekday from 100, so every change is easy to recompute."""
    days = [start + timedelta(n) for n in range((end - start).days + 1) if (start + timedelta(n)).weekday() < 5]
    return [(d, 100 + i * step) for i, d in enumerate(days)]


@pytest.mark.parametrize(("day", "months", "expected"), [
    (date(2026, 3, 31), 1, date(2026, 2, 28)), (date(2024, 3, 31), 1, date(2024, 2, 29)),
    (date(2026, 5, 31), 3, date(2026, 2, 28)), (date(2026, 9, 23), 12, date(2025, 9, 23)),
    (date(2026, 1, 31), -1, date(2026, 2, 28))])
def test_months_back_clamps_to_month_end(day: date, months: int, expected: date) -> None:
    assert periods.months_back(day, months) == expected


def test_change_uses_last_bar_on_or_before_and_null_before_history() -> None:
    series = weekday_series(date(2026, 1, 5), date(2026, 3, 31))
    moved = periods.change(series, date(2026, 3, 31), date(2026, 3, 1))  # Sunday → Friday 27 Feb
    base = periods.last_on_or_before(series, date(2026, 2, 27))
    assert moved["base_date"] == date(2026, 2, 27)
    assert moved["pct"] == round((series[-1][1] / base[1] - 1) * 100, 2)
    assert periods.change(series, date(2026, 3, 31), date(2025, 12, 31)) == {
        "pct": None, "base_date": None, "base_value": None, "end_value": series[-1][1]}


def test_calendar_vs_fiscal_ytd() -> None:
    as_of = date(2026, 9, 23)
    assert periods.ytd_base(as_of, "calendar") == date(2025, 12, 31)
    assert periods.ytd_base(as_of, "fiscal") == date(2026, 6, 30)
    assert periods.ytd_base(date(2026, 3, 10), "fiscal") == date(2025, 6, 30)
    assert periods.ytd_base(date(2026, 6, 30), "fiscal") == date(2025, 6, 30)  # "before AS_OF"
    series = weekday_series(date(2025, 1, 1), as_of)
    cal, fis = (periods.changes(series, as_of, b)["ytd"] for b in ("calendar", "fiscal"))
    assert cal["base_date"] == date(2025, 12, 31) and fis["base_date"] == date(2026, 6, 30)
    assert cal["pct"] > fis["pct"] > 0


def test_fiscal_year_labels() -> None:
    assert periods.bucket(date(2025, 7, 1), "Y", "fiscal") == ("FY2026", date(2025, 7, 1), date(2026, 6, 30))
    assert periods.bucket(date(2026, 6, 30), "Y", "fiscal")[0] == "FY2026"
    assert periods.bucket(date(2026, 7, 1), "Y", "fiscal")[0] == "FY2027"
    assert periods.bucket(date(2025, 8, 15), "Q", "fiscal") == ("FY2026 Q1", date(2025, 7, 1), date(2025, 9, 30))
    assert periods.bucket(date(2026, 2, 1), "Q", "fiscal")[0] == "FY2026 Q3"
    assert periods.bucket(date(2026, 2, 1), "Q", "calendar") == ("2026 Q1", date(2026, 1, 1), date(2026, 3, 31))
    assert periods.bucket(date(2026, 2, 1), "M", "fiscal") == ("2026-02", date(2026, 2, 1), date(2026, 2, 28))
    assert periods.bucket(date(2025, 3, 3), "Y", "calendar") == ("2025", date(2025, 1, 1), date(2025, 12, 31))


def test_returns_buckets_partial_oldest_first_and_null_without_history() -> None:
    as_of = date(2026, 9, 23)
    series = weekday_series(date(2025, 11, 10), as_of)
    buckets = periods.returns(series, as_of, "M", "calendar")
    assert [b["label"] for b in buckets] == [f"2025-{m}" for m in (11, 12)] + [f"2026-{m:02d}" for m in range(1, 10)]
    assert buckets[0]["pct"] is None  # previous month end (31 Oct) is before the first bar
    assert all(b["pct"] is not None for b in buckets[1:])
    assert [b["partial"] for b in buckets] == [False] * 10 + [True]
    end_aug = periods.last_on_or_before(series, date(2026, 8, 31))[1]
    assert buckets[-1]["pct"] == round((series[-1][1] / end_aug - 1) * 100, 2)
    assert len(periods.returns(weekday_series(date(2016, 1, 1), as_of), as_of, "Y", "fiscal")) == 10
    assert len(periods.returns(weekday_series(date(2016, 1, 1), as_of), as_of, "Q", "calendar")) == 12


def test_rebase_to_100_on_first_common_date() -> None:
    symbol = [(date(2026, 1, d), v) for d, v in ((5, 50.0), (6, 55.0), (7, 60.0))]
    bench = [(date(2026, 1, d), v) for d, v in ((6, 200.0), (7, 210.0))]
    assert periods.rebase(symbol, bench, None) == [(date(2026, 1, 6), 100.0, 100.0), (date(2026, 1, 7), 109.09, 105.0)]
    assert periods.rebase(symbol, bench, date(2026, 1, 6)) == [(date(2026, 1, 7), 100.0, 100.0)]
    assert periods.window_start(date(2026, 10, 9), "ALL") is None
