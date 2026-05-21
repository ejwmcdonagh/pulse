from typing import Annotated

from fastapi import APIRouter, Query

from app.db.client import get_db
from app.models.enums import RiskDomain, SignalSource

router = APIRouter(prefix="/api/signals", tags=["signals"])


@router.get("")
async def list_signals(
    source: Annotated[SignalSource | None, Query()] = None,
    risk_domain: Annotated[RiskDomain | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    """
    List signals with optional filtering.

    risk_domain uses a Postgres array containment check (@>) - it matches any
    signal whose risk_domains array contains the requested domain, not an
    exact equality match. A signal tagged [identity_credential, vulnerability_patch]
    will be returned when filtering by either domain.
    """
    db = get_db()
    query = db.table("signals").select("*").order("published_at", desc=True).range(offset, offset + limit - 1)

    if source:
        query = query.eq("source", source.value)
    if risk_domain:
        # PostgREST array containment filter
        query = query.contains("risk_domains", [risk_domain.value])

    result = query.execute()
    return {"signals": result.data, "offset": offset, "limit": limit}


@router.get("/stats")
async def signal_stats():
    """
    Counts grouped by source and risk domain - used by the dashboard to
    populate domain swim-lane headers before card data is loaded.
    """
    db = get_db()
    result = db.table("signals").select("source, risk_domains").execute()

    source_counts: dict[str, int] = {}
    domain_counts: dict[str, int] = {}

    for row in result.data:
        src = row["source"]
        source_counts[src] = source_counts.get(src, 0) + 1
        for domain in row.get("risk_domains", []):
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

    return {"by_source": source_counts, "by_domain": domain_counts}


@router.get("/{signal_id}")
async def get_signal(signal_id: str):
    db = get_db()
    result = db.table("signals").select("*").eq("id", signal_id).single().execute()
    return result.data
