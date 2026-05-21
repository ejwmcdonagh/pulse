"""
Reset cards and clusters for re-running the pipeline.

Two modes:

  python3 scripts/reset_cards.py
    Deletes all cards and resets cluster status to pending.
    Use this when you only want to re-run card generation with an updated prompt.
    Clusters stay intact so clustering does not need to re-run.

  python3 scripts/reset_cards.py --full
    Deletes all cards AND all clusters.
    Use this for a full fresh pipeline run (clustering + card generation).
    Signals are freed so clusters/run will re-cluster everything from scratch.

Run from backend/ with the venv active.
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.client import get_db


def main():
    full = "--full" in sys.argv
    db = get_db()

    cards = db.table("provocation_cards").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
    print(f"Deleted {len(cards.data)} cards")

    if full:
        clusters = db.table("signal_clusters").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
        print(f"Deleted {len(clusters.data)} clusters (full reset - re-run clusters/run next)")
    else:
        clusters = db.table("signal_clusters").update({"status": "pending"}).neq("status", "dismissed").execute()
        print(f"Reset {len(clusters.data)} clusters to pending (cards/run will regenerate cards)")


if __name__ == "__main__":
    main()
