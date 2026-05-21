"""
Backfill risk_domains for all signals using the current domain_mapper rules.

Run this whenever new domains are added to domain_mapper.py. Signals ingested
before the domain change have stale risk_domains and won't appear in the new
domain's clustering pass.

Run from backend/ with the venv active:
    python scripts/backfill_domains.py

Safe to re-run - every row is updated regardless of current value.
Processes in batches of 500 to avoid holding large result sets in memory.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.client import get_db
from app.domain_mapper import map_domains

PAGE_SIZE = 500


def main() -> None:
    db = get_db()

    # Count total for progress reporting
    count_result = db.table("signals").select("id", count="exact").execute()
    total = count_result.count or 0
    print(f"Total signals to backfill: {total}")

    updated = 0
    offset = 0

    while True:
        result = (
            db.table("signals")
            .select("id, title, summary, tags")
            .range(offset, offset + PAGE_SIZE - 1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            break

        for row in rows:
            new_domains = map_domains(
                row.get("title") or "",
                row.get("summary"),
                row.get("tags") or [],
            )
            db.table("signals").update(
                {"risk_domains": [d.value for d in new_domains]}
            ).eq("id", row["id"]).execute()
            updated += 1

        print(f"  {updated}/{total} processed...")
        offset += PAGE_SIZE

        if len(rows) < PAGE_SIZE:
            break

    print(f"Done. Updated {updated} signals.")


if __name__ == "__main__":
    main()
