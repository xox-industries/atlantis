from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from fastapi import FastAPI

if TYPE_CHECKING:
    from asyncpg import Pool as PgPool
    from redis.asyncio import Redis
    from supabase import AClient as SupabaseClient

    from src.persistence import Persistence

class App(FastAPI):
    env: Literal["production", "development"]
    supabase: SupabaseClient
    redis: Redis
    persistence: Persistence
    supabase_database_pool: PgPool
