"""
Abstract base for all signal ingesters.

Every source implements this interface. The separation means:
- New sources can be added without touching existing ingesters
- The scheduler and API trigger can call any ingester identically
- Testing can exercise the persistence logic independently of HTTP fetching
"""

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

from app.db.client import get_db
from app.models.enums import SignalSource
from app.models.signal import Signal

logger = logging.getLogger(__name__)


class BaseIngester(ABC):
    source: SignalSource  # must be set on each subclass

    async def run(self) -> int:
        """
        Fetch signals from the source and persist new ones to the DB.
        Returns the count of newly inserted signals.

        Records a row in ingestion_runs for every execution — success or failure —
        so operators can audit exactly when each source was last polled.
        """
        db = get_db()
        run_id = self._start_run(db)

        try:
            signals = await self.fetch()
            inserted = self._upsert(db, signals)
            self._complete_run(db, run_id, inserted)
            logger.info("Ingestion complete: source=%s inserted=%d", self.source, inserted)
            return inserted
        except Exception as exc:
            self._fail_run(db, run_id, str(exc))
            logger.exception("Ingestion failed: source=%s", self.source)
            raise

    @abstractmethod
    async def fetch(self) -> list[Signal]:
        """Fetch and parse raw source data into Signal objects."""
        ...

    # ── Private helpers ────────────────────────────────────────────────────────

    def _start_run(self, db: Any) -> str:
        result = (
            db.table("ingestion_runs")
            .insert({
                "source": self.source,
                "started_at": datetime.now(UTC).isoformat(),
                "status": "running",
            })
            .execute()
        )
        return result.data[0]["id"]

    def _complete_run(self, db: Any, run_id: str, inserted: int) -> None:
        db.table("ingestion_runs").update({
            "completed_at": datetime.now(UTC).isoformat(),
            "signals_ingested": inserted,
            "status": "success",
        }).eq("id", run_id).execute()

    def _fail_run(self, db: Any, run_id: str, error: str) -> None:
        db.table("ingestion_runs").update({
            "completed_at": datetime.now(UTC).isoformat(),
            "status": "failed",
            "error_message": error[:2000],  # guard against very long tracebacks
        }).eq("id", run_id).execute()

    def _upsert(self, db: Any, signals: list[Signal]) -> int:
        """
        Insert signals, ignoring rows that already exist (same source + source_id).
        We use ignore_duplicates rather than an update because once a signal is
        ingested its raw_data should be treated as immutable — card generation
        may already reference it. If the source corrects a record, it'll get
        a new source_id.
        """
        if not signals:
            return 0

        rows = [
            {
                **s.model_dump(mode="json"),
                # Supabase-py sends arrays as Python lists — Postgres accepts them fine,
                # but JSONB columns need explicit serialisation
                "risk_domains": [d.value for d in s.risk_domains],
            }
            for s in signals
        ]

        result = (
            db.table("signals")
            .upsert(rows, on_conflict="source,source_id", ignore_duplicates=True)
            .execute()
        )
        return len(result.data) if result.data else 0
