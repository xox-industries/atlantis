from __future__ import annotations

from typing import TYPE_CHECKING

from asyncpg import Pool as PgPool

from src.persistence.mixin.supabase_user import SupabaseUserPersistence

if TYPE_CHECKING:
    from src.app import App


class Persistence(
    SupabaseUserPersistence,
):
    def __init__(self, app: App, pool: PgPool, /) -> None:
        super().__init__(app, pool=pool)
