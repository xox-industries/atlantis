from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.palworld import PalworldInstance


@strawberry.type
class DisplayPalworldType:
    @strawberry.field
    async def display_palworld(
        self,
        info: Info["AppContext"],
    ) -> list[PalworldInstance]:
        palworld = info.context.app.palworld
        names = await palworld.ls()
        return [
            PalworldInstance(
                name=name,
                running=await palworld.is_running(name),
                port=await palworld.get_port(name),
            )
            for name in names
        ]
