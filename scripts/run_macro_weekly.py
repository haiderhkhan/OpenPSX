"""P6-06: build this ISO week's (PKT) macro brief as of AS_OF and write data/macro/macro_<week>.json.

Reads data/openpsx.db read-only. Uses the LLM unless FEATURE_MACRO_LLM=false (then the template).
Usage: python scripts/run_macro_weekly.py
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))  # run as a script: make `backend` importable

from backend.agents import macro  # noqa: E402


def main() -> int:
    m = macro.generate()
    path = macro.write(m)
    print(f"{path.relative_to(ROOT).as_posix()}: {m.week} as of {m.as_of_date} -> {m.stance} ({m.status})")
    print(f"  indicators: {m.indicators.model_dump()}")
    print(f"  brief: {m.brief}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
