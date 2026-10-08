from __future__ import annotations

from collections.abc import AsyncGenerator

import strawberry
from strawberry.types import Info

from src.route.context import AppContext


@strawberry.type
class SubscribePalworldType:
    @strawberry.subscription
    async def palworld_validate_app(
        self,
        path: str,
        info: Info[AppContext],
    ) -> AsyncGenerator[str]:
        return await info.context.app.palworld.validate_app(path)
