"""P2-05: manual CSV/Excel import into a copy of the fixture DB (AS_OF 2026-10-09)."""
from __future__ import annotations

import json
import shutil
import sqlite3
from contextlib import closing
from datetime import datetime
from pathlib import Path

import pytest
from openpyxl import Workbook

from scripts import import_manual as im

KINDS = ["prices", "kmi30_history", "fundamentals", "macro", "corporate_actions", "news"]
EXAMPLE = "# e.g. "


@pytest.fixture
def db(fixture_db: Path, tmp_path: Path) -> Path:
    """A private copy: imports must never touch the shared session fixture."""
    return Path(shutil.copy(fixture_db, tmp_path / "openpsx.db"))


def _csv(tmp_path: Path, text: str, name: str = "in.csv") -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _query(db: Path, sql: str, *args) -> list[tuple]:
    with closing(sqlite3.connect(db)) as conn:
        return conn.execute(sql, args).fetchall()


@pytest.mark.parametrize("kind", KINDS)
def test_every_template_imports_with_its_examples(kind: str, db: Path, tmp_path: Path) -> None:
    template = (im.TEMPLATES / f"{kind}.csv").read_text(encoding="utf-8")
    assert im.import_file(kind, im.TEMPLATES / f"{kind}.csv", db)["errors"] == []  # header only: 0 rows
    examples = [line[len(EXAMPLE):] for line in template.splitlines() if line.startswith(EXAMPLE)]
    assert examples, f"{kind}.csv needs at least one '{EXAMPLE}' row"
    result = im.import_file(kind, _csv(tmp_path, template + "\n".join(examples) + "\n"), db)
    assert result["errors"] == []
    assert sum(result["counts"].values()) == len(examples)
    assert not any(status == "ignored" for _, status in result["counts"])


def test_bad_rows_are_rejected_with_line_numbers_and_nothing_is_written(db: Path, tmp_path: Path) -> None:
    path = _csv(tmp_path, "symbol,date,close\n"
                          "OGDC,2026-09-01,100\n"      # line 2: fine
                          "XXXX,2026-09-01,100\n"      # line 3: unknown symbol
                          "OGDC,2026-10-12,100\n"      # line 4: after AS_OF 2026-10-09
                          "OGDC,2026-02-30,100\n"      # line 5: not a real date
                          "OGDC,01/09/2026,100\n"      # line 6: wrong format
                          "OGDC,2026-09-02,-5\n"       # line 7: close must be > 0
                          "OGDC,2026-09-01,101\n")     # line 8: duplicate of line 2
    errors = im.import_file("prices", path, db)["errors"]
    assert [e.split(":")[0] for e in errors] == [f"line {n}" for n in range(3, 9)]
    assert "unknown symbol 'XXXX'" in errors[0] and "after AS_OF_DATE 2026-10-09" in errors[1]
    assert "duplicate of line 2" in errors[5]
    assert _query(db, "SELECT COUNT(*) FROM prices_daily WHERE source = 'manual'")[0][0] == 0


def test_missing_column_is_reported_on_the_header_line(db: Path, tmp_path: Path) -> None:
    path = _csv(tmp_path, "# comment\nsymbol,date\nOGDC,2026-09-01\n")
    assert im.import_file("prices", path, db)["errors"] == ["line 2: missing column(s) close"]


def test_dry_run_reports_counts_but_writes_nothing(db: Path, tmp_path: Path) -> None:
    sql = "SELECT close, adj_close, source FROM prices_daily WHERE symbol = 'OGDC' AND date = '2026-09-01'"
    before = _query(db, sql)
    path = _csv(tmp_path, "symbol,date,close\nOGDC,2026-09-01,123.45\nKMI30,2026-09-01,150000\n")
    result = im.import_file("prices", path, db, dry_run=True)
    assert result["counts"] == {("OGDC", "replaced"): 1, ("KMI30", "replaced"): 1}
    assert _query(db, sql) == before


def test_price_import_replaces_the_row_and_is_re_adjusted(db: Path, tmp_path: Path) -> None:
    # Fixture: LUCK has a 10% bonus on 2025-03-03, so a manual close before it must be adjusted by 1/1.1.
    path = _csv(tmp_path, "symbol,date,open,high,low,close,volume\nLUCK,2025-02-28,540,560,530,550,1000\n")
    assert im.import_file("prices", path, db)["errors"] == []
    close, adj, source = _query(db, "SELECT close, adj_close, source FROM prices_daily "
                                    "WHERE symbol = 'LUCK' AND date = '2025-02-28'")[0]
    assert (close, source) == (550, "manual") and adj == pytest.approx(550 / 1.1)


def test_official_bonus_re_runs_the_adjustment(db: Path, tmp_path: Path) -> None:
    path = _csv(tmp_path, "symbol,ex_date,action_type,value\nOGDC,2026-06-01,BONUS,25\n")
    assert im.import_file("corporate_actions", path, db)["errors"] == []
    ratios = dict(_query(db, "SELECT date, adj_close / close FROM prices_daily WHERE symbol = 'OGDC' "
                             "AND date IN ('2026-05-29', '2026-06-01')"))
    assert ratios["2026-05-29"] == pytest.approx(1 / 1.25) and ratios["2026-06-01"] == pytest.approx(1.0)


def test_news_dedupes_on_url_and_uses_the_symbol_column(db: Path, tmp_path: Path) -> None:
    url = "https://www.brecorder.com/news/1/a"
    path = _csv(tmp_path, "published_at,source,title,url,symbol\n"
                          f"2026-09-10,BR,Banks and E&P stocks rally,{url},OGDC\n"
                          f"2026-09-10,BR,Banks and E&P stocks rally,{url},MEBL\n"             # same URL: merged
                          "2026-10-12,,Meezan Bank posts record profit,https://dawn.com/b,\n")  # past AS_OF; aliases
    assert im.import_file("news", path, db)["errors"] == []
    rows = {u: (json.loads(s), src, p) for u, s, src, p in _query(db, "SELECT url, symbols, source, published_at FROM news")}
    assert rows[url] == (["MEBL", "OGDC"], "BR", "2026-09-10T00:00:00+05:00")
    assert rows["https://dawn.com/b"][:2] == (["MEBL"], "MANUAL")
    # Re-import: the known URL takes the file's symbols; no second row.
    again = _csv(tmp_path, f"published_at,title,url,symbol\n2026-09-10,Other title,{url},LUCK\n", "again.csv")
    assert im.import_file("news", again, db)["counts"] == {("LUCK", "replaced"): 1}
    assert _query(db, "SELECT symbols FROM news WHERE url = ?", url) == [('["LUCK"]',)]


def test_news_rejects_bad_source_and_url(db: Path, tmp_path: Path) -> None:
    path = _csv(tmp_path, "published_at,source,title,url\n2026-09-10,PROFIT,T,https://x.pk/a\n"
                          "2026-09-10,BR,T2,not-a-link\n")
    errors = im.import_file("news", path, db)["errors"]
    assert errors[0].startswith("line 2: source 'PROFIT'") and errors[1].startswith("line 3: url")


def test_macro_may_run_past_as_of_and_defaults_release_date(db: Path, tmp_path: Path) -> None:
    path = _csv(tmp_path, 'series,date,value\nCPI_YOY,2026-10-31,4.5\nPKR_USD,2026-10-12,"1,281.25"\n')
    assert im.import_file("macro", path, db)["errors"] == []
    assert _query(db, "SELECT series, value, release_date FROM macro_series WHERE source = 'manual' ORDER BY 1") == [
        ("CPI_YOY", 4.5, "2026-11-05"), ("PKR_USD", 1281.25, "2026-10-12")]


def test_xlsx_with_excel_dates_imports(db: Path, tmp_path: Path) -> None:
    book = Workbook()
    book.active.append(["Symbol", "Date", "Close"])
    book.active.append(["mebl", datetime(2026, 9, 1), 222.5])
    book.active.append(["MEBL", datetime(2026, 10, 12), 230])  # line 3: after AS_OF
    book.save(tmp_path / "in.xlsx")
    assert im.import_file("prices", tmp_path / "in.xlsx", db)["errors"] == [
        "line 3: date 2026-10-12 is after AS_OF_DATE 2026-10-09"]
    book.active.delete_rows(3)
    book.save(tmp_path / "in.xlsx")
    assert im.import_file("prices", tmp_path / "in.xlsx", db)["counts"] == {("MEBL", "replaced"): 1}
