import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Literal, cast

import redis.asyncio as aioredis
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import _MiddlewareFactory
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL

from src.app import App
from src.route import create_context, create_schema

ENV: Literal["development", "production"] = cast(
    "Literal['development', 'production']",
    os.getenv("ENV", "development"),
)


@asynccontextmanager
async def lifespan(app: App) -> AsyncGenerator[None]:
    app.redis = aioredis.from_url(
        os.environ["REDIS_URL"],
        decode_responses=False,
    )

    yield

    await app.redis.aclose(close_connection_pool=True)


app = App(lifespan=lifespan)

app.add_middleware(
    middleware_class=cast("_MiddlewareFactory", CORSMiddleware),
    allow_credentials=True,
    allow_headers=[
        "Authorization",
        "Content-Type",
    ],
    allow_methods=[
        "*",
    ],
    allow_origins=[os.environ["WEB_URL"]] if ENV == "production" else "*",
)

app.include_router(
    router=GraphQLRouter(
        schema=create_schema(),
        context_getter=create_context(app, env=ENV),
        multipart_uploads_enabled=True,
        subscription_protocols=[GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL],
    ),
    prefix="/graphql",
)

app.add_api_route(path="/health", endpoint=lambda: {"status": "healthy"})
