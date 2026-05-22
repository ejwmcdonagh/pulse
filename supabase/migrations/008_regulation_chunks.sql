-- Regulation knowledge base for RAG at card generation time.
--
-- Stores pre-chunked regulation articles with OpenAI text-embedding-3-small vectors
-- (1536 dims). At card generation time, the cluster summary is embedded and the
-- top-5 most similar chunks are retrieved via the RPC function below and injected
-- into the Claude prompt to ground the compliance_gap field in real regulatory text.
--
-- Populated by scripts/index_regulations.py - run that after applying this migration.

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE regulation_chunks (
    id          UUID        PRIMARY KEY DEFAULT gen_random_uuid(),
    regulation  TEXT        NOT NULL,
    article_ref TEXT        NOT NULL,
    title       TEXT        NOT NULL,
    content     TEXT        NOT NULL,
    embedding   vector(512),
    indexed_at  TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- IVFFlat with 10 lists is appropriate for a small static corpus (40-60 rows).
-- The pattern scales if the corpus grows without requiring a schema change.
CREATE INDEX idx_regulation_chunks_embedding
    ON regulation_chunks
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 10);

-- PostgREST does not expose the <=> vector distance operator, so similarity
-- search must go through an RPC function called via db.rpc() in Python.
CREATE OR REPLACE FUNCTION search_regulation_chunks(
    query_embedding vector(512),
    match_count     integer DEFAULT 5
)
RETURNS TABLE (
    id          UUID,
    regulation  TEXT,
    article_ref TEXT,
    title       TEXT,
    content     TEXT,
    similarity  float
)
LANGUAGE sql STABLE AS $$
    SELECT
        id,
        regulation,
        article_ref,
        title,
        content,
        1 - (embedding <=> query_embedding) AS similarity
    FROM regulation_chunks
    WHERE embedding IS NOT NULL
    ORDER BY embedding <=> query_embedding
    LIMIT match_count;
$$;
