"""
Database client.

Uses supabase-py, which wraps PostgREST - so this works against any
Postgres instance that has PostgREST in front of it, not just Supabase.
The service role key bypasses row-level security for backend writes;
never expose it client-side.
"""

from functools import lru_cache

from supabase import Client, create_client

from app.config import settings


@lru_cache(maxsize=1)
def get_db() -> Client:
    """Return a cached Supabase client. Thread-safe for read operations."""
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
