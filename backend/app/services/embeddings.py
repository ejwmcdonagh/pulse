"""
Voyage AI embedding generation and regulation chunk retrieval for RAG.

Voyage AI is Anthropic's recommended embedding partner and has a free tier
(200M tokens, no credit card required). Model: voyage-3-lite (1024 dims).

Both public functions degrade gracefully: if VOYAGE_API_KEY is not set or any
call fails, they return None / [] so card generation always continues unblocked.
"""

import logging
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

_VOYAGE_EMBEDDINGS_URL = "https://api.voyageai.com/v1/embeddings"
_EMBEDDING_MODEL = "voyage-3-lite"


def generate_embedding(text: str) -> list[float] | None:
    """Return a 1024-dim embedding vector, or None if the key is absent or the call fails."""
    if not settings.voyage_api_key:
        return None

    import time

    for attempt in range(4):
        try:
            response = httpx.post(
                _VOYAGE_EMBEDDINGS_URL,
                headers={
                    "Authorization": f"Bearer {settings.voyage_api_key}",
                    "Content-Type": "application/json",
                },
                json={"model": _EMBEDDING_MODEL, "input": [text]},
                timeout=30.0,
            )
            if response.status_code == 429:
                wait = 30 * (attempt + 1)
                logger.warning("Rate limited by Voyage AI - waiting %ds (attempt %d/4)", wait, attempt + 1)
                time.sleep(wait)
                continue
            response.raise_for_status()
            return response.json()["data"][0]["embedding"]
        except httpx.HTTPStatusError:
            raise
        except Exception:
            logger.exception("Embedding API call failed")
            return None

    logger.error("Embedding failed after 4 attempts (rate limit)")
    return None


def search_regulations(
    db: Any,
    query: str,
    match_count: int = 5,
) -> list[dict[str, Any]]:
    """
    Embed query text and retrieve the most relevant regulation chunks by cosine similarity.

    Uses db.rpc() because PostgREST doesn't expose the pgvector <=> distance operator.
    Returns [] if OPENAI_API_KEY is absent, embedding fails, or the DB call fails.
    """
    embedding = generate_embedding(query)
    if embedding is None:
        return []

    try:
        result = db.rpc(
            "search_regulation_chunks",
            {"query_embedding": embedding, "match_count": match_count},
        ).execute()
        return result.data or []
    except Exception:
        logger.exception("Regulation chunk search failed")
        return []
