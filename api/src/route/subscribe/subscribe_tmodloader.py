from __future__ import annotations

from collections.abc import AsyncGenerator

import strawberry
from strawberry.types import Info

from src.route.context import AppContext


@strawberry.type
class SubscribeTModLoaderType:
    @strawberry.subscription
    async def tmodloader_validate_app(
        self,
        path: str,
        info: Info[AppContext],
    ) -> AsyncGenerator[str]:
        return await info.context.app.tmodloader.validate_app(path)

    @strawberry.subscription
    async def stop_tmodloader(
        self,
        path: str,
        info: Info[AppContext],
    ) -> AsyncGenerator[str]:
        return info.context.app.tmodloader.stop(path)
