"""P4-01: the weekly panel (SCHEMA §6) on a copy of the fixture DB, plus macro rows the fixture lacks."""
from __future__ import annotations

import shutil
from contextlib import closing
from datetime import date
from pathlib import Path

import pandas as pd
import pytest

from backend import config
from backend.db.connection import connect_ro, connect_rw
from backend.ml.features import FEATURES, build_panel

AS_OF = date(2026, 10, 9)
T = pd.Timestamp("2025-06-13")  # a Friday: week end t of the look-ahead test
NEXT = pd.Timestamp("2025-06-20")
MACRO = [  # series, date, value, release_date. The 11.0 rate is observed before t but released after it.
    ("POLICY_RATE", "2025-01-27", 12.0, "2025-01-27"),
    ("POLICY_RATE", "2025-06-10", 11.0, "2025-06-16"),
    ("CPI_YOY", "2025-04-30", 3.5, "2025-05-05"),
    ("CPI_YOY", "2025-05-31", 3.2, "2025-06-05"),
    ("PKR_USD", "2025-05-12", 280.1, "2025-05-12"),
    ("PKR_USD", "2025-06-12", 281.0, "2025-06-12"),
    ("PKR_USD", "2025-06-20", 282.0, "2025-06-20"),
]


@pytest.fixture
def db(fixture_db: Path, tmp_path: Path) -> Path:
    path = Path(shutil.copy(fixture_db, tmp_path / "openpsx.db"))
    with closing(connect_rw(path)) as conn:
        conn.executemany("INSERT INTO macro_series VALUES (?, ?, ?, ?, 'test')", MACRO)
        conn.commit()
    return path


def panel(path: Path) -> pd.DataFrame:
    with closing(connect_ro(path)) as conn:
        return build_panel(conn, AS_OF)


def test_changing_data_after_week_t_leaves_features_at_t_unchanged(db: Path) -> None:
    before = panel(db)
    with closing(connect_rw(db)) as conn:
        conn.execute("UPDATE prices_daily SET adj_close = adj_close * (1.5 + (rowid % 7) / 10.0), "
                     "volume = volume * 3 WHERE date > ?", (T.date().isoformat(),))
        conn.execute("UPDATE macro_series SET value = value + 5 WHERE release_date > ?", (T.date().isoformat(),))
        conn.commit()
    after = panel(db)

    cols = ["symbol", "date", *FEATURES]
    old, new = (p.loc[p["date"] <= T, cols].reset_index(drop=True) for p in (before, after))
    assert len(old) > 4 * 52
    pd.testing.assert_frame_equal(old, new, check_exact=True)
    assert not before.loc[before["date"] > T, cols].equals(after.loc[after["date"] > T, cols])  # the edit bit


def test_panel_is_one_row_per_symbol_week(db: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    p = panel(db)
    iso = p["date"].dt.isocalendar()
    last = p.groupby("symbol").tail(1)

    assert set(p["symbol"]) == {"OGDC", "LUCK", "MEBL", "MZNPETF"}  # KMI30 only feeds idx_*
    assert not pd.concat([p["symbol"], iso["year"], iso["week"]], axis=1).duplicated().any()
    assert p["date"].max() == pd.Timestamp(AS_OF)
    assert last.loc[last["symbol"] == "MZNPETF", "date"].item() == pd.Timestamp("2026-08-04")  # stopped ETF
    assert last["y"].isna().all() and p.drop(last.index)["y"].isin([0.0, 1.0]).all()
    assert p.groupby("symbol")["is_etf"].first().to_dict() == {"LUCK": 0, "MEBL": 0, "MZNPETF": 1, "OGDC": 0}

    monkeypatch.setattr(config, "FEATURE_ETFS", False)
    assert "MZNPETF" not in set(panel(db)["symbol"])


def test_feature_values_follow_definitions(db: Path) -> None:
    p = panel(db).set_index(["symbol", "date"])
    with closing(connect_ro(db)) as conn:
        adj = dict(conn.execute("SELECT date, adj_close FROM prices_daily WHERE symbol = 'OGDC'").fetchall())
    at_t, at_next = p.loc[("OGDC", T)], p.loc[("OGDC", NEXT)]

    assert at_t["ret_1w"] == pytest.approx((adj["2025-06-13"] / adj["2025-06-06"] - 1) * 100)  # 5 weekdays back
    assert at_t["y"] == float(adj["2025-06-20"] > adj["2025-06-13"])
    assert at_t["rel_strength_12w"] == pytest.approx(at_t["ret_12w"] - at_t["idx_ret_12w"])
    # Macro as released by t: the 11.0 rate (observed 06-10) is invisible until its 06-16 release.
    assert (at_t["policy_rate"], at_t["policy_rate_chg_12w"], at_t["cpi_yoy"]) == (12.0, 0.0, 3.2)
    assert (at_next["policy_rate"], at_next["policy_rate_chg_12w"]) == (11.0, -1.0)
    assert at_t["pkr_usd_chg_4w"] == pytest.approx((281.0 / 280.1 - 1) * 100)
    assert at_next["pkr_usd_chg_4w"] == pytest.approx((282.0 / 280.1 - 1) * 100)
