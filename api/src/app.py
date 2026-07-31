from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from fastapi import FastAPI

if TYPE_CHECKING:
    from redis.asyncio import Redis


class App(FastAPI):
    env: Literal["production", "development"]
    redis: Redis
