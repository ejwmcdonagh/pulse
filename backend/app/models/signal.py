from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.models.enums import RiskDomain, Severity, SignalSource, SignalType


class Signal(BaseModel):
    """
    Canonical signal model. Matches the `signals` table schema exactly so
    instances can be serialised directly for DB inserts.
    """

    source: SignalSource
    source_id: str
    signal_type: SignalType
    title: str
    summary: str | None = None
    published_at: datetime | None = None
    severity: Severity | None = None
    cvss_score: float | None = None
    risk_domains: list[RiskDomain] = []
    tags: list[str] = []
    raw_data: dict[str, Any]
    url: str | None = None


class SignalRecord(Signal):
    """Signal as returned from the DB — includes server-assigned fields."""

    id: UUID
    ingested_at: datetime


class IngestionRunRecord(BaseModel):
    id: UUID
    source: SignalSource
    started_at: datetime
    completed_at: datetime | None
    signals_ingested: int
    status: str
    error_message: str | None
