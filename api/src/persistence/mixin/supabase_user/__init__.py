from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

from asyncpg import Connection as PgConnection
from asyncpg import Pool as PgPool
from asyncpg import Record as PgRecord
from fastapi import HTTPException, status
from supabase_auth import User as SupabaseUser

if TYPE_CHECKING:
    from src.app import App

from src.persistence.mixin import AbstractPersistence

__all__: list[str] = [
    "SupabaseUserPersistence",
]


def _parse_metadata(raw: str | dict[str, Any] | None) -> dict[str, Any]:
    if raw is None:
        return {}
    if isinstance(raw, str):
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    return raw


class SupabaseUserPersistence(AbstractPersistence):
    def __init__(self, app: App, /, pool: PgPool) -> None:
        super().__init__(app, pool=pool)

    async def _construct_supabase_user(self, schema: PgRecord, /) -> SupabaseUser:
        return SupabaseUser(
            id=str(schema["id"]),
            email=schema["email"],
            aud=schema["aud"] or "authenticated",
            app_metadata=_parse_metadata(schema["raw_app_meta_data"]),
            user_metadata=_parse_metadata(schema["raw_user_meta_data"]),
            created_at=schema["created_at"],
        )

    async def find_supabase_user_by_id(self, user_id: str | UUID, /) -> SupabaseUser:
        async def __query(client: PgConnection) -> PgRecord:
            row = cast(
                "PgRecord | None",
                await client.fetchrow(
                    """
                    SELECT id, email, aud, created_at, raw_app_meta_data, raw_user_meta_data
                    FROM auth.users
                    WHERE id = $1
                    LIMIT 1
                    """,
                    str(user_id),
                ),
            )
            if row is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
            return row

        row = await self._commit(__query)
        return await self._construct_supabase_user(row)

    async def find_supabase_user_by_email(
        self,
        email: str,
        /,
    ) -> SupabaseUser | None:
        async def __query(client: PgConnection) -> PgRecord | None:
            return cast(
                "PgRecord | None",
                await client.fetchrow(
                    """
                    SELECT id, email, aud, created_at, raw_app_meta_data, raw_user_meta_data
                    FROM auth.users
                    WHERE LOWER(email) = LOWER($1)
                    LIMIT 1
                    """,
                    email,
                ),
            )

        row = await self._commit(__query)
        if row is None:
            return None
        return await self._construct_supabase_user(row)
