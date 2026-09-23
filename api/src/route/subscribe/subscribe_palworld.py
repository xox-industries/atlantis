from collections.abc import AsyncGenerator

import strawberry
from strawberry.types import Info

from src.route.context import AppContext


@strawberry.type
class SubscribePalworldType:
    @strawberry.subscription
    async def palworld_validate_app(self, info: Info["AppContext"]) -> AsyncGenerator[str]:
        palworld = info.context.app.palworld
        return await palworld.validate_app()
