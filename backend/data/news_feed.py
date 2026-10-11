"""
Pakistan financial news headline fetcher via RSS.

Sources are PK-specific business press. VERIFY these feed URLs still resolve
before your demo - RSS endpoints on news sites shift without notice, and
conference wifi is not the place to discover that.

If a feed is unreachable during the demo, falls back to a small set of
neutral mock headlines so the Geo-Sentiment agent always has *something* to
reason over rather than erroring out mid-debate.
"""

from __future__ import annotations

FEEDS = {
    "Business Recorder": "https://www.brecorder.com/feeds/business",  # VERIFY before demo
    "Profit (Pakistan Today)": "https://profit.pakistantoday.com.pk/feed/",  # VERIFY before demo
    "Dawn Business": "https://www.dawn.com/feeds/business",  # VERIFY before demo
}

_MOCK_HEADLINES = [
    {"source": "mock", "title": "SBP holds policy rate steady amid stable inflation outlook", "published": "recent"},
    {"source": "mock", "title": "IMF review mission concludes talks, cites continued reform progress", "published": "recent"},
    {"source": "mock", "title": "PKR trades in a narrow band against the dollar this week", "published": "recent"},
]


def get_headlines(query: str = "", limit: int = 5) -> list[dict]:
    """Fetch recent PK business headlines, optionally filtered by `query` substring."""
    try:
        import feedparser
        results = []
        for source, url in FEEDS.items():
            parsed = feedparser.parse(url)
            for entry in parsed.entries[:limit]:
                if not query or query.lower() in entry.title.lower():
                    results.append({
                        "source": source,
                        "title": entry.title,
                        "published": getattr(entry, "published", "unknown"),
                    })
        return results[:limit] if results else _MOCK_HEADLINES
    except Exception:
        return _MOCK_HEADLINES
