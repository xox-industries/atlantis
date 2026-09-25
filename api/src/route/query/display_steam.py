from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.steam import SteamAccount


@strawberry.type
class DisplaySteamType:
    @strawberry.field
    async def display_steam(
        self,
        info: Info["AppContext"],
    ) -> SteamAccount:
        return SteamAccount(username=info.context.app.steam.account)
