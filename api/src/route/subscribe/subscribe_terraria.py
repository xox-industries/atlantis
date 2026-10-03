from __future__ import annotations

from collections.abc import AsyncGenerator

import strawberry
from strawberry.types import Info

from src.route.context import AppContext


@strawberry.type
class SubscribeTerrariaType:
    @strawberry.subscription
    async def terraria_validate_app(
        self,
        path: str,
        info: Info[AppContext],
    ) -> AsyncGenerator[str]:
        return await info.context.app.terraria.validate_app(path)

    @strawberry.subscription
    async def stop_terraria(
        self,
        path: str,
        info: Info[AppContext],
    ) -> AsyncGenerator[str]:
        return info.context.app.terraria.stop(path)
