-- Migration 001: Core signal storage schema
--
-- Signals are the atomic unit of ingestion. Every piece of threat intel,
-- advisory, or vulnerability data lands here before any processing.
-- raw_data preserves the full source payload so card generation can
-- reference original source content without re-fetching.

CREATE TABLE signals (
    id           UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source       TEXT        NOT NULL,
    -- Original identifier from the source system (CVE ID, advisory slug, etc.)
    source_id    TEXT        NOT NULL,
    signal_type  TEXT        NOT NULL,
    title        TEXT        NOT NULL,
    summary      TEXT,
    published_at TIMESTAMPTZ,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    severity     TEXT,
    cvss_score   DECIMAL(3, 1),
    -- One signal can map to multiple risk domains (e.g. a credential CVE
    -- belongs to both identity_credential and vulnerability_patch)
    risk_domains TEXT[]      NOT NULL DEFAULT '{}',
    tags         TEXT[]      NOT NULL DEFAULT '{}',
    raw_data     JSONB       NOT NULL,
    url          TEXT,
    -- Prevents duplicate rows on repeated ingestion runs
    UNIQUE (source, source_id)
);

COMMENT ON TABLE signals IS 'Raw ingested signals from all threat intelligence and regulatory sources.';
COMMENT ON COLUMN signals.source IS 'Originating source: cisa_kev | cisa_advisory | ncsc | nvd';
COMMENT ON COLUMN signals.signal_type IS 'Signal category: vulnerability | advisory | threat_intel | regulatory';
COMMENT ON COLUMN signals.risk_domains IS 'Mapped risk domains from domain_mapper. Array — signals can span multiple domains.';
COMMENT ON COLUMN signals.raw_data IS 'Full source payload. Preserved for provocation card generation prompts.';

-- Track every ingestion run for debugging and observability
CREATE TABLE ingestion_runs (
    id               UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    source           TEXT        NOT NULL,
    started_at       TIMESTAMPTZ NOT NULL,
    completed_at     TIMESTAMPTZ,
    signals_ingested INTEGER     NOT NULL DEFAULT 0,
    status           TEXT        NOT NULL,
    -- Populated on failure — include stack trace or HTTP error detail
    error_message    TEXT
);

COMMENT ON TABLE ingestion_runs IS 'Audit log for each ingestion execution. status: running | success | failed';

CREATE INDEX idx_signals_source       ON signals (source);
CREATE INDEX idx_signals_risk_domains ON signals USING GIN (risk_domains);
CREATE INDEX idx_signals_published_at ON signals (published_at DESC);
CREATE INDEX idx_signals_ingested_at  ON signals (ingested_at DESC);
CREATE INDEX idx_ingestion_runs_source ON ingestion_runs (source, started_at DESC);
