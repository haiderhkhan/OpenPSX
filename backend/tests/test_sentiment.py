"""News matching/selection and the sentiment agent: offline, private fixture DB, scripted fake LLM."""
from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

import pytest

from backend import config
from backend.agents import lexicon, llm, sentiment as sa
from backend.agents.validators import validation_errors
from backend.ingest import news
from scripts import make_fixture_db

AS_OF = make_fixture_db.AS_OF.isoformat()  # 2026-10-09 → window 2026-09-09 … 2026-10-09
MATCHERS = news.build_matchers([
    ("LUCK", ["Lucky Cement Limited", "Lucky Cement", "Lucky"]),
    ("OGDC", ["Oil & Gas Development Company", "OGDCL"]),
    ("MEBL", ["Meezan Bank Limited", "Meezan Bank", "Meezan"]),
    ("MZNPETF", ["Meezan Pakistan ETF", "Meezan ETF"]),
    ("EFERT", ["Engro Fertilizers", "Engro Fert"]),
    ("ENGROH", ["Engro Holdings", "Engro Corporation", "Engro"]),
    ("SYS", ["Systems Limited", "Systems Ltd"]),
    ("KMI30", ["kmi 30", "kmi30", "kmi", "kmi-30"]),
])


# --- Alias matching ---
@pytest.mark.parametrize(("title", "symbols"), [
    ("Lucky Cement posts higher quarterly profit", ["LUCK"]),
    ("LUCK shares rally on cement demand", ["LUCK"]),
    ("Lucky Cement's exports rise", ["LUCK"]),
    ("A lucky break for textile exporters", []),          # false-positive guard: one-word name alone
    ("Lucky streak continues for the rupee", []),
    ("Good luck to the new SBP governor", []),            # tickers are case-sensitive
    ("OGDCL output up; Oil & Gas Development Company adds well", ["OGDC"]),
    ("Meezan Bank profit doubles", ["MEBL"]),
    ("Meezan ETF sees inflows", ["MZNPETF"]),
    ("Meezan launches new product", []),
    ("Engro Fertilizers urea offtake", ["EFERT"]),
    ("Engro to expand", []),
    ("Systems Limited signs deal; IT systems upgraded", ["SYS"]),
    ("KMI-30 gains 500 points", ["KMI30"]),
])
def test_alias_matching(title: str, symbols: list[str]) -> None:
    assert news.match_symbols(title, MATCHERS) == symbols


# --- Feed parsing + storage ---
RSS = b"""<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Lucky Cement  posts profit</title><link>https://x.test/a</link>
  <pubDate>Wed, 23 Sep 2026 20:30:00 +0000</pubDate></item>
<item><title>No date here</title><link>https://x.test/b</link></item>
</channel></rss>"""


def test_parse_feed_converts_to_pkt_and_skips_undated() -> None:
    assert news.parse_feed(RSS, "DAWN") == [{"source": "DAWN", "title": "Lucky Cement posts profit",
                                             "url": "https://x.test/a", "published_at": "2026-09-24T01:30:00+05:00"}]


@pytest.fixture
def db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = make_fixture_db.build(tmp_path / "openpsx.db")
    monkeypatch.setattr(config, "DB_PATH", path)
    return path


def _add(db: Path, rows: list[tuple[str, str, str]]) -> None:
    """rows of (day, title, url); symbols are matched with the fixture DB's aliases."""
    items = [{"source": "MANUAL", "published_at": f"{d}T10:00:00+05:00", "title": t, "url": u} for d, t, u in rows]
    with closing(sqlite3.connect(db)) as conn, conn:
        news.insert_items(conn, items, news.load_matchers(conn))


def _select(db: Path, symbol: str) -> list[dict]:
    with closing(sqlite3.connect(db)) as conn:
        return news.select_headlines(conn, symbol, AS_OF)


def test_insert_dedupes_by_url_and_by_title_time(db: Path) -> None:
    _add(db, [("2026-10-01", "OGDC profit rises", "https://x.test/1")])
    _add(db, [("2026-10-01", "OGDC profit rises", "https://x.test/1"),       # same URL
              ("2026-10-01", "OGDC profit rises", "https://x.test/other")])  # same title + time
    with closing(sqlite3.connect(db)) as conn:
        assert conn.execute("SELECT COUNT(*), MAX(symbols) FROM news").fetchone() == (1, '["OGDC"]')


def test_selection_window_is_inclusive_and_capped_at_as_of(db: Path) -> None:
    assert news.window(AS_OF) == ("2026-09-09", AS_OF)
    _add(db, [("2026-09-08", "OGDC too old", "u0"), ("2026-09-09", "OGDC first day", "u1"),
              (AS_OF, "OGDC on AS_OF", "u2"), ("2026-10-10", "OGDC after AS_OF", "u3"), ("2026-10-01", "MEBL news", "u4")])
    assert [h["date"] for h in _select(db, "OGDC")] == [AS_OF, "2026-09-09"]


def test_selection_keeps_the_10_newest(db: Path) -> None:
    _add(db, [(f"2026-09-{d}", f"OGDC item {d}", f"v{d}") for d in range(10, 25)])
    got = _select(db, "OGDC")
    assert len(got) == 10 and got[0]["date"] == "2026-09-24" and got[-1]["date"] == "2026-09-15"


# --- Agent ---
OGDC_NEWS = [("2026-10-08", "OGDC posts record quarterly profit", "a1"),
             ("2026-10-05", "OGDCL output rises on new wells", "a2"),
             ("2026-10-02", "OGDC faces gas price concern", "a3"),
             ("2026-09-20", "OGDC board approves dividend", "a4")]


class FakeLLM:
    def __init__(self, monkeypatch: pytest.MonkeyPatch, *outcomes) -> None:
        self.outcomes, self.payloads = list(outcomes), []
        monkeypatch.setattr(llm, "generate_json", self)

    def __call__(self, agent, prompt_version, system, payload, schema, max_tokens):
        assert (agent, prompt_version, max_tokens) == ("sentiment", "sent-v1", 220)
        self.payloads.append(payload)
        out = self.outcomes.pop(0)
        if isinstance(out, Exception):
            raise out
        return out(payload) if callable(out) else out


def _cites(p: dict) -> dict:
    ids = [h["id"] for h in p["headlines"]]
    return {"stance": "POSITIVE", "reasons": [f"Reports of higher profit and output [#{ids[0]}] [#{ids[1]}].",
                                              f"{p['n_headlines']} headlines since {p['window_start']}."]}


@pytest.fixture
def ogdc(db: Path) -> Path:
    _add(db, OGDC_NEWS + [("2026-10-01", "Lucky Cement expands capacity", "b1"),
                          ("2026-10-03", "Lucky Cement profit up", "b2")])
    return db


def test_live_result_with_python_evidence_then_cached(ogdc: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    fake = FakeLLM(monkeypatch, _cites)
    res = sa.run("ogdc")
    p = fake.payloads[0]
    assert (res.agent, res.status, res.stance) == ("sentiment", "LIVE", "POSITIVE")
    assert [h["date"] for h in p["headlines"]] == ["2026-10-08", "2026-10-05", "2026-10-02", "2026-09-20"]
    assert res.evidence == {"n_headlines": 4, "window_start": "2026-09-09", "window_end": AS_OF,
                            "lexicon_score": sum(lexicon.score(t) for _, t, _ in OGDC_NEWS),
                            "headline_ids": ", ".join(str(h["id"]) for h in p["headlines"])}
    assert sa.run("OGDC").status == "CACHED" and len(fake.payloads) == 1


def test_template_from_lexicon_when_llm_is_down(ogdc: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    FakeLLM(monkeypatch, llm.LLMDisabled("off"))
    res = sa.run("OGDC")
    assert (res.status, res.stance) == ("TEMPLATE", "POSITIVE")  # record, profit, rises, dividend vs concern
    assert any("[#" in r for r in res.reasons)


def test_bad_citation_retries_then_templates(ogdc: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    bad = {"stance": "POSITIVE", "reasons": ["Strong coverage [#999]."]}
    fake = FakeLLM(monkeypatch, bad, bad)
    assert sa.run("OGDC").status == "TEMPLATE"
    assert "999" in fake.payloads[1]["previous_error"]


def test_template_text_passes_the_validators(ogdc: Path) -> None:
    with closing(sqlite3.connect(ogdc)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM symbols WHERE symbol = 'OGDC'").fetchone()
        payload = sa.build_payload(row, AS_OF, news.select_headlines(conn, "OGDC", AS_OF))
    assert validation_errors(sa.template(payload), payload, sa.RESPONSE_SCHEMA) == []


@pytest.mark.parametrize(("symbol", "n", "text"), [("LUCK", 2, "Only 2"), ("MEBL", 0, "No recent coverage")])
def test_too_few_headlines_abstains_without_llm(ogdc: Path, monkeypatch: pytest.MonkeyPatch,
                                                symbol: str, n: int, text: str) -> None:
    fake = FakeLLM(monkeypatch)
    res = sa.run(symbol)
    assert (res.status, res.stance, res.evidence["n_headlines"]) == ("UNAVAILABLE", "NEUTRAL", n)
    assert text in res.reasons[0] and fake.payloads == []


@pytest.mark.parametrize("symbol", ["MZNPETF", "KMI30", "NOPE"])
def test_etfs_index_and_unknowns_are_rejected(db: Path, symbol: str) -> None:
    with pytest.raises(sa.NotInScope):
        sa.run(symbol)


def test_no_feed_fetching_in_the_backend() -> None:
    """R-16: only scripts/ fetch feeds; backend code never imports an HTTP client or feedparser outside news.py."""
    for p in (config.ROOT / "backend").rglob("*.py"):
        if "tests" in p.parts or "voice" in p.parts:  # voice/ calls Groq (P7-03)
            continue
        text = p.read_text(encoding="utf-8")
        assert "httpx" not in text, p
        assert "feedparser" not in text or p.name == "news.py", p
