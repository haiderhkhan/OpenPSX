"""Single-screen Streamlit demo for the PSX War Room."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

import streamlit as st

from agents_app.fundamentals import RESERVED_KEYS
from agents_app.moderator import ModeratorVerdict, analyze_ticker
from agents_app.schema import SignalOutput


SIGNAL_COLORS = {
    "BULLISH": "#15803d",
    "BEARISH": "#b91c1c",
    "NEUTRAL": "#6b7280",
}
DISPLAY_NAMES = {
    "quant": "Quant",
    "macro": "Macro",
    "geo_sentiment": "Geo-Sentiment",
    "fundamentals": "Fundamentals",
}


@st.cache_data
def available_tickers() -> list[str]:
    """Read demo tickers from the fixture without treating metadata as tickers."""

    fixture_path = Path(__file__).resolve().parent / "data" / "fundamentals_mock.json"
    with fixture_path.open("r", encoding="utf-8") as fixture_file:
        payload = json.load(fixture_file)
    return sorted(
        ticker
        for ticker, record in payload.items()
        if ticker not in RESERVED_KEYS and isinstance(record, dict)
    )


def signal_badge(signal: str) -> str:
    color = SIGNAL_COLORS.get(signal, SIGNAL_COLORS["NEUTRAL"])
    return (
        f'<span style="color: {color}; font-weight: 700; '
        f'letter-spacing: 0.04em;">{signal}</span>'
    )


def render_signal(output: SignalOutput) -> None:
    st.markdown(signal_badge(output.signal.value), unsafe_allow_html=True)
    st.caption(f"Confidence: {output.confidence:.1f}")
    st.write(output.basis)


def render_specialist_card(
    name: str, output: SignalOutput | None, exclusion_reason: str | None
) -> None:
    with st.container(border=True):
        st.subheader(DISPLAY_NAMES[name])
        if output is not None:
            render_signal(output)
        else:
            st.markdown(
                '<span style="color: #9ca3af; font-weight: 700;">EXCLUDED</span>',
                unsafe_allow_html=True,
            )
            st.caption(exclusion_reason or "No validated signal returned.")


def render_verdict(verdict: ModeratorVerdict) -> None:
    st.subheader("War Room Verdict")
    with st.container(border=True):
        render_signal(verdict.overall)

    st.subheader("Specialist Views")
    columns = st.columns(2)
    for index, name in enumerate(("quant", "macro", "geo_sentiment", "fundamentals")):
        with columns[index % 2]:
            render_specialist_card(
                name,
                verdict.specialists.get(name),
                verdict.exclusions.get(name),
            )


def main() -> None:
    st.set_page_config(page_title="PSX War Room", layout="wide")
    st.title("PSX War Room")
    st.caption("A multi-agent directional research read for Pakistan Stock Exchange tickers.")

    ticker = st.selectbox("PSX ticker", available_tickers())
    if st.button("Analyze", type="primary"):
        with st.spinner(f"Convening the council for {ticker}..."):
            try:
                verdict = asyncio.run(analyze_ticker(ticker))
            except Exception as error:
                st.error(f"The analysis could not start: {error}")
            else:
                render_verdict(verdict)

    st.divider()
    st.caption(
        "Research tool only - not financial advice, no price targets, and running on mock data."
    )


if __name__ == "__main__":
    main()