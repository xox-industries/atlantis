from __future__ import annotations

from collections.abc import AsyncGenerator

import strawberry
from strawberry.types import Info

from src.route.context import AppContext


@strawberry.type
class SubscribeValheimType:
    @strawberry.subscription
    async def valheim_validate_app(
        self,
        info: Info["AppContext"],
    ) -> AsyncGenerator[str]:
        return await info.context.app.valheim.validate_app()
