"""
ICO (Information Commissioner's Office) enforcement actions ingester.

Source: https://ico.org.uk
Feed:   https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/rss/

The ICO is the UK data protection regulator. Its enforcement actions are the
most direct evidence available that a specific type of security failure results
in a real financial penalty. A fine for inadequate access controls is far more
compelling in a board talking point than citing GDPR Article 32 in the abstract.

These signals map strongly to the data_exposure and identity_credential domains
and provide the compliance gap and board talking point layers with concrete
regulatory consequence data.
"""

from datetime import UTC
from email.utils import parsedate_to_datetime

import feedparser

from app.domain_mapper import map_domains
from app.http import async_client
from app.ingestion.base import BaseIngester
from app.models.enums import SignalSource, SignalType
from app.models.signal import Signal
from app.severity_mapper import infer_severity

FEED_URL = "https://ico.org.uk/about-the-ico/media-centre/news-and-blogs/rss/"


class IcoEnforcementIngester(BaseIngester):
    source = SignalSource.ICO_ENFORCEMENT

    async def fetch(self) -> list[Signal]:
        async with async_client(timeout=30) as client:
            resp = await client.get(FEED_URL)
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        return [s for entry in feed.entries if (s := self._parse(entry)) is not None]

    def _parse(self, entry: dict) -> Signal | None:
        title: str = entry.get("title", "").strip()
        if not title:
            return None

        summary: str = entry.get("summary", "")
        link: str = entry.get("link", "")
        source_id = link.rstrip("/").split("/")[-1] if link else title[:100]

        published_at = None
        if pub := entry.get("published"):
            try:
                published_at = parsedate_to_datetime(pub).astimezone(UTC)
            except Exception:
                pass

        tags = [t.get("term", "") for t in entry.get("tags", []) if t.get("term")]
        tags.append("regulatory")
        tags.append("enforcement")

        return Signal(
            source=SignalSource.ICO_ENFORCEMENT,
            source_id=source_id,
            signal_type=SignalType.REGULATORY,
            title=title,
            summary=summary,
            published_at=published_at,
            severity=infer_severity(title, summary),
            risk_domains=map_domains(title, summary, tags),
            tags=tags,
            url=link or None,
            raw_data={"title": title, "summary": summary, "link": link, "published": entry.get("published", "")},
        )
