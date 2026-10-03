from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.valheim import ValheimInstance


@strawberry.type
class DisplayValheimType:
    @strawberry.field
    async def display_valheim(
        self,
        info: Info["AppContext"],
    ) -> list[ValheimInstance]:
        valheim = info.context.app.valheim
        names = await valheim.ls()
        return [
            ValheimInstance(
                name=name,
                container_name=valheim.get_container_name(name),
                running=await valheim.is_running(name),
                port=await valheim.get_port(name),
            )
            for name in names
        ]
