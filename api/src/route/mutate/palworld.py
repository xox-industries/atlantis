from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.palworld import PalworldInstance


@strawberry.type
class MutationPalworldType:
    @strawberry.mutation
    async def create_palworld(
        self,
        info: Info["AppContext"],
    ) -> PalworldInstance:
        name = await info.context.app.palworld.create_instance()
        return PalworldInstance(
            name=name,
            container_name=info.context.app.palworld.get_container_name(name),
            running=False,
            port=None,
        )

    @strawberry.mutation
    async def start_palworld(
        self,
        instance: str,
        info: Info["AppContext"],
    ) -> PalworldInstance:
        container = await info.context.app.palworld.start(instance)
        port = await info.context.app.docker.get_host_port(container)
        return PalworldInstance(
            name=instance,
            container_name=info.context.app.palworld.get_container_name(instance),
            running=True,
            port=port,
        )

    @strawberry.mutation
    async def stop_palworld(
        self,
        instance: str,
        info: Info["AppContext"],
    ) -> PalworldInstance:
        await info.context.app.palworld.stop(instance)
        return PalworldInstance(
            name=instance,
            container_name=info.context.app.palworld.get_container_name(instance),
            running=False,
            port=None,
        )
