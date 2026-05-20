"""
NVD (National Vulnerability Database) CVE ingester.

Source: https://nvd.nist.gov/
API:    https://services.nvd.nist.gov/rest/json/cves/2.0

We pull CRITICAL severity CVEs published in the last 30 days. The 30-day window
is intentional — it's long enough to catch slow-burning issues while keeping
the signal volume manageable. The NVD API supports date range filtering so we
don't have to pull the full database.

Rate limiting: without an API key, NVD allows ~5 requests per 30 seconds.
With a free API key (NVD_API_KEY env var), this increases to ~50 req/30s.
We add a sleep between paginated requests to stay within the unauthenticated
limit rather than silently fail if the key isn't set.

Why CRITICAL only? NVD has ~30,000 CVEs in a 30-day window. CRITICAL (CVSS ≥9.0)
is roughly 3–5% of that and represents the overlap of high severity + high
exploitability that maps to the product's card-triggering threshold.
"""

import asyncio
from datetime import UTC, datetime, timedelta

from app.config import settings
from app.http import async_client
from app.domain_mapper import map_domains
from app.ingestion.base import BaseIngester
from app.models.enums import Severity, SignalSource, SignalType
from app.models.signal import Signal

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
# NVD returns max 2000 results per page; 100 is a safer default for CRITICAL filtering
PAGE_SIZE = 100
# Seconds to wait between paginated requests when no API key is set
UNAUTHENTICATED_SLEEP = 6


def _cvss_score(cve: dict) -> float | None:
    """Extract the highest available CVSS base score from a CVE record."""
    metrics = cve.get("metrics", {})
    # Prefer v3.1 → v3.0 → v2 in that order
    for key in ("cvssMetricV31", "cvssMetricV30", "cvssMetricV2"):
        entries = metrics.get(key, [])
        if entries:
            return entries[0].get("cvssData", {}).get("baseScore")
    return None


def _severity(score: float | None) -> Severity | None:
    if score is None:
        return None
    if score >= 9.0:
        return Severity.CRITICAL
    if score >= 7.0:
        return Severity.HIGH
    if score >= 4.0:
        return Severity.MEDIUM
    return Severity.LOW


class NvdIngester(BaseIngester):
    source = SignalSource.NVD

    async def fetch(self) -> list[Signal]:
        # NVD date range filter uses ISO 8601 with UTC offset
        now = datetime.now(UTC)
        # NVD API v2 expects timestamps without a timezone suffix
        pub_start = (now - timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%S.000")
        pub_end = now.strftime("%Y-%m-%dT%H:%M:%S.000")

        headers = {}
        if settings.nvd_api_key:
            headers["apiKey"] = settings.nvd_api_key

        signals: list[Signal] = []
        start_index = 0

        async with async_client(timeout=30, headers=headers) as client:
            while True:
                params = {
                    "cvssV3Severity": "CRITICAL",
                    "pubStartDate": pub_start,
                    "pubEndDate": pub_end,
                    "startIndex": start_index,
                    "resultsPerPage": PAGE_SIZE,
                }
                resp = await client.get(NVD_API_URL, params=params)
                resp.raise_for_status()
                data = resp.json()

                for vuln in data.get("vulnerabilities", []):
                    if signal := self._parse(vuln.get("cve", {})):
                        signals.append(signal)

                total = data.get("totalResults", 0)
                start_index += PAGE_SIZE

                if start_index >= total:
                    break

                # Respect rate limits — sleep longer if no key is configured
                sleep_s = 0.5 if settings.nvd_api_key else UNAUTHENTICATED_SLEEP
                await asyncio.sleep(sleep_s)

        return signals

    def _parse(self, cve: dict) -> Signal | None:
        cve_id: str = cve.get("id", "")
        if not cve_id:
            return None

        # NVD descriptions array is ordered: English first when present
        descriptions = cve.get("descriptions", [])
        en_desc = next((d["value"] for d in descriptions if d.get("lang") == "en"), "")

        score = _cvss_score(cve)
        severity = _severity(score)

        # Pull CVE references as tags — source URLs, vendor bulletins etc.
        ref_tags = [r.get("source", "") for r in cve.get("references", []) if r.get("source")]

        return Signal(
            source=SignalSource.NVD,
            source_id=cve_id,
            signal_type=SignalType.VULNERABILITY,
            title=cve_id,
            summary=en_desc,
            published_at=_parse_dt(cve.get("published")),
            severity=severity,
            cvss_score=score,
            risk_domains=map_domains(cve_id, en_desc, ref_tags),
            tags=ref_tags[:10],  # cap tag count to avoid bloat
            url=f"https://nvd.nist.gov/vuln/detail/{cve_id}",
            raw_data=cve,
        )


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
