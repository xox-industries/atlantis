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
        names = await palworld.list_instances()
        return [
            PalworldInstance(
                name=name,
                container_name=palworld.get_container_name(name),
                running=await palworld.is_running(name),
                port=await palworld.get_host_port(name),
            )
            for name in names
        ]
