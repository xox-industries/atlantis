from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

from asyncpg import Connection as PgConnection
from asyncpg import Pool as PgPool
from asyncpg import Record as PgRecord
from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from src.app import App


@dataclass(frozen=True)
class PaginationParams:
    limit: int
    offset: int


@dataclass(frozen=True)
class SortParams:
    field: str
    direction: str


@dataclass(frozen=True)
class PaginatedResult[T]:
    items: list[T]
    total_count: int


class AbstractPersistence:
    def __init__(self, app: App, /, pool: PgPool) -> None:
        self._app: App = app
        self._pool: PgPool = pool

    async def _commit[T](self, command: Callable[[PgConnection], Coroutine[Any, Any, T]], /) -> T:
        async with self._pool.acquire() as client, client.transaction():
            return await command(client)

    async def _fetch_paginated(
        self,
        client: PgConnection,
        sql: str,
        params: tuple[Any, ...],
        /,
        limit: int,
        offset: int,
    ) -> tuple[list[PgRecord], int]:
        """Run a paginated query and return the matching rows plus total count.

        `sql` must be a SELECT statement without a trailing semicolon. LIMIT/OFFSET
        are appended safely using indexed parameters.
        """
        paginated_sql = f"{sql} LIMIT ${len(params) + 1} OFFSET ${len(params) + 2}"
        rows = cast(
            "list[PgRecord]",
            await client.fetch(paginated_sql, *params, limit, offset),
        )
        total = cast(
            "int",
            await client.fetchval(f"SELECT COUNT(*) FROM ({sql}) AS q", *params),  # noqa: S608
        )
        return rows, total


class AbstractPersistedModel[U](BaseModel, ABC):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    @staticmethod
    @abstractmethod
    async def construct_model(app: App, schema: U, /) -> AbstractPersistedModel: ...
