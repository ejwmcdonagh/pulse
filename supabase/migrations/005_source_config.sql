-- Add disabled_sources to org_profile so users can toggle any built-in source.
-- Stored as a text array of source IDs (e.g. '{cisa_kev, nvd}').
-- Empty array means all sources are enabled (the default).

ALTER TABLE org_profile
  ADD COLUMN disabled_sources TEXT[] NOT NULL DEFAULT '{}';
