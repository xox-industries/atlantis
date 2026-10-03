import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Literal, cast

import asyncpg
import redis.asyncio as aioredis
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import _MiddlewareFactory
from strawberry.fastapi import GraphQLRouter
from strawberry.subscriptions import GRAPHQL_TRANSPORT_WS_PROTOCOL, GRAPHQL_WS_PROTOCOL
from supabase import AsyncClientOptions
from supabase import create_async_client as create_supabase_client

from src.app import App
from src.apt import Apt
from src.docker import Docker
from src.minecraft_java_edition import MinecraftJavaEdition
from src.palworld import Palworld
from src.persistence import Persistence
from src.route import create_context, create_schema
from src.steam import Steam
from src.terraria import Terraria
from src.tmodloader import TModLoader
from src.valheim import Valheim

ENV: Literal["development", "production"] = cast(
    "Literal['development', 'production']",
    os.getenv("ENV", "development"),
)


@asynccontextmanager
async def lifespan(app: App) -> AsyncGenerator[None]:
    app.supabase = await create_supabase_client(
        supabase_url=os.environ["SUPABASE_URL"],
        supabase_key=os.environ["SUPABASE_SECRET_KEY"],
        options=AsyncClientOptions(storage_client_timeout=8000),
    )
    app.supabase_database_pool = await asyncpg.create_pool(
        os.environ["SUPABASE_DB_URL"],
        min_size=1,
        max_size=15,
        max_inactive_connection_lifetime=300,
        command_timeout=300,
    )
    app.redis = aioredis.from_url(
        os.environ["REDIS_URL"],
        decode_responses=False,
    )
    app.persistence = Persistence(app, app.supabase_database_pool)
    app.apt = Apt(app)
    app.steam = Steam(app)
    app.docker = Docker(app)
    app.minecraft_java_edition = MinecraftJavaEdition(app)
    app.palworld = Palworld(app)
    app.terraria = Terraria(app)
    app.tmodloader = TModLoader(app)
    app.valheim = Valheim(app)

    await app.ensure_wineprefix()

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
    allow_origins="*",
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
