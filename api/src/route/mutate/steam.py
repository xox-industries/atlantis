from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext


@strawberry.type
class MutationSteamType:
    @strawberry.mutation
    async def steam_logout(
        self,
        info: Info["AppContext"],
    ) -> bool:
        await info.context.app.steam.logout()
        return True
