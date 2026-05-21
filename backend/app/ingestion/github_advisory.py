"""
GitHub Security Advisories ingester.

Source: https://github.com/advisories
API:    https://api.github.com/advisories

GitHub's advisory database covers the open source ecosystem broadly - npm,
PyPI, Go, Maven, RubyGems, NuGet, and more. It is the primary signal source
for the supply_chain domain.

No authentication required for read access. Rate limit is 60 requests/hour
unauthenticated. We pull CRITICAL and HIGH severity advisories published in
the last 30 days to stay within that limit with a single paginated request.

If a GITHUB_TOKEN env var is set, the rate limit increases to 5,000 req/hour.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.domain_mapper import map_domains
from app.http import async_client
from app.ingestion.base import BaseIngester
from app.models.enums import Severity, SignalSource, SignalType
from app.models.signal import Signal
from app.severity_mapper import infer_severity

API_URL = "https://api.github.com/advisories"
PAGE_SIZE = 100
# Unauthenticated rate limit is 60 req/hour. Cap pages to stay safe.
# With a GITHUB_TOKEN this can be raised - see config.py.
MAX_PAGES_UNAUTHENTICATED = 5
MAX_PAGES_AUTHENTICATED = 50


_SEVERITY_MAP = {
    "CRITICAL": Severity.CRITICAL,
    "HIGH": Severity.HIGH,
    "MODERATE": Severity.MEDIUM,
    "LOW": Severity.LOW,
}


class GithubAdvisoryIngester(BaseIngester):
    source = SignalSource.GITHUB_ADVISORY

    async def fetch(self) -> list[Signal]:
        now = datetime.now(UTC)
        cutoff = now - timedelta(days=30)

        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        github_token = getattr(settings, "github_token", "")
        if github_token:
            headers["Authorization"] = f"Bearer {github_token}"

        signals: list[Signal] = []
        page = 1
        max_pages = MAX_PAGES_AUTHENTICATED if github_token else MAX_PAGES_UNAUTHENTICATED

        async with async_client(timeout=30, headers=headers) as client:
            while page <= max_pages:
                params = {
                    "type": "reviewed",
                    "per_page": PAGE_SIZE,
                    "page": page,
                    "direction": "desc",
                    "sort": "published",
                }
                resp = await client.get(API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

                if not data:
                    break

                stop = False
                for advisory in data:
                    # Filter to CRITICAL and HIGH only in Python
                    sev = (advisory.get("severity") or "").upper()
                    if sev not in ("CRITICAL", "HIGH"):
                        continue
                    # Stop once we go past the 30-day window
                    pub = advisory.get("published_at", "")
                    if pub:
                        try:
                            pub_dt = datetime.fromisoformat(pub.replace("Z", "+00:00"))
                            if pub_dt < cutoff:
                                stop = True
                                break
                        except ValueError:
                            pass
                    if signal := self._parse(advisory):
                        signals.append(signal)

                if stop or len(data) < PAGE_SIZE:
                    break

                page += 1
                await asyncio.sleep(1)

        return signals

    def _parse(self, advisory: dict) -> Signal | None:
        ghsa_id: str = advisory.get("ghsa_id", "")
        if not ghsa_id:
            return None

        title: str = advisory.get("summary", ghsa_id)
        description: str = advisory.get("description", "")
        severity_str: str = (advisory.get("severity") or "").upper()
        severity = _SEVERITY_MAP.get(severity_str) or infer_severity(title, description)

        # Collect affected ecosystems as tags - useful for supply chain domain mapping
        ecosystems = [
            v.get("package", {}).get("ecosystem", "")
            for v in advisory.get("vulnerabilities", [])
            if v.get("package", {}).get("ecosystem")
        ]
        cve_ids = advisory.get("cve_id") or []
        if isinstance(cve_ids, str):
            cve_ids = [cve_ids]

        tags = list(set(ecosystems))
        tags += [c for c in cve_ids if c]

        published_at = None
        if pub := advisory.get("published_at"):
            try:
                published_at = datetime.fromisoformat(pub.replace("Z", "+00:00"))
            except ValueError:
                pass

        return Signal(
            source=SignalSource.GITHUB_ADVISORY,
            source_id=ghsa_id,
            signal_type=SignalType.VULNERABILITY,
            title=title,
            summary=description[:1000],
            published_at=published_at,
            severity=severity,
            cvss_score=advisory.get("cvss", {}).get("score") if advisory.get("cvss") else None,
            risk_domains=map_domains(title, description, tags),
            tags=tags[:10],
            url=advisory.get("html_url"),
            raw_data=advisory,
        )
