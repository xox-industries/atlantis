from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.valheim import ValheimInstance


@strawberry.type
class MutationValheimType:
    @strawberry.mutation
    async def create_valheim(
        self,
        info: Info["AppContext"],
    ) -> ValheimInstance:
        name = await info.context.app.valheim.touch()
        return ValheimInstance(
            name=name,
            container_name=info.context.app.valheim.get_container_name(name),
            running=False,
            port=None,
        )

    @strawberry.mutation
    async def start_valheim(
        self,
        instance: str,
        info: Info["AppContext"],
    ) -> ValheimInstance:
        container = await info.context.app.valheim.start(instance)
        port = await info.context.app.docker.get_host_port(container)
        return ValheimInstance(
            name=instance,
            container_name=info.context.app.valheim.get_container_name(instance),
            running=True,
            port=port,
        )

    @strawberry.mutation
    async def stop_valheim(
        self,
        instance: str,
        info: Info["AppContext"],
    ) -> ValheimInstance:
        await info.context.app.valheim.stop(instance)
        return ValheimInstance(
            name=instance,
            container_name=info.context.app.valheim.get_container_name(instance),
            running=False,
            port=None,
        )
