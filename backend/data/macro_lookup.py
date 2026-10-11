"""
Hardcoded macro snapshot for Pakistan.

There's no clean free real-time API for SBP policy rate / CPI / PKR-USD, so
for hackathon purposes this is a manually-refreshed lookup table rather than
a live scraper - faster to ship, and just as accurate since these figures
move on the order of weeks, not minutes.

UPDATE THESE VALUES the morning of your demo from sbp.org.pk and pbs.gov.pk.
"""

from __future__ import annotations

MACRO_SNAPSHOT = {
    "policy_rate_pct": 11.0,            # SBP policy rate - CHECK sbp.org.pk before demo
    "cpi_yoy_pct": 4.5,                 # latest YoY inflation - CHECK pbs.gov.pk
    "pkr_usd": 283.5,                   # interbank rate - CHECK sbp.org.pk
    "imf_program_status": "Active EFF program, reviews on track",  # CHECK latest IMF PK statement
    "fx_reserves_usd_bn": 12.0,
    "as_of": "UPDATE THIS DATE before your demo",
}

# Rough directional sensitivity per sector to interest rate moves.
# Tune these based on what you actually know about each sector - this is a
# starting point, not gospel.
SECTOR_RATE_SENSITIVITY = {
    "Banking": "high_positive",      # higher rates generally help bank NIMs
    "Cement": "high_negative",       # rate-sensitive, capex-heavy
    "Textile": "medium_negative",    # export sector, more FX-sensitive than rate-sensitive
    "Fertilizer": "low",
    "E&P": "low",
    "Technology": "medium_negative",
}


def get_macro_snapshot(sector: str | None = None) -> dict:
    """Return the current macro snapshot, optionally with sector rate-sensitivity."""
    snapshot = dict(MACRO_SNAPSHOT)
    if sector:
        snapshot["sector_rate_sensitivity"] = SECTOR_RATE_SENSITIVITY.get(sector, "unknown")
    return snapshot
