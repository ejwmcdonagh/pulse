"""
Dump current clusters to stdout for before/after comparison.

Run from backend/ with the venv active:
  python3 scripts/dump_clusters.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.client import get_db


def main():
    db = get_db()
    result = (
        db.table("signal_clusters")
        .select("risk_domain, risk_vector, cluster_summary, score, signal_count, source_count, severity_max, status, metadata")
        .neq("status", "dismissed")
        .order("score", desc=True)
        .execute()
    )
    clusters = result.data or []

    print(f"Total clusters: {len(clusters)}\n")

    # Group by domain for easy scanning
    by_domain: dict[str, list] = {}
    for c in clusters:
        by_domain.setdefault(c["risk_domain"], []).append(c)

    for domain, rows in sorted(by_domain.items()):
        print(f"=== {domain.upper()} ({len(rows)} clusters) ===")
        for c in rows:
            breakdown = c.get("metadata", {}).get("score_breakdown", {})
            sources_pts = breakdown.get("source_diversity", "?")
            print(
                f"  [{c['score']:.0f}] {c['risk_vector']}\n"
                f"       signals={c['signal_count']} sources={c['source_count']} "
                f"severity={c['severity_max'] or 'n/a'} status={c['status']}\n"
                f"       {c['cluster_summary']}"
            )
        print()


if __name__ == "__main__":
    main()
