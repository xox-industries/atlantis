from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.palworld import PalworldInstance, PalworldManifest


@strawberry.type
class MutationPalworldType:
    @strawberry.mutation
    async def create_palworld(
        self,
        info: Info[AppContext],
        *,
        steam_app_beta_branch: str | None = None,
    ) -> PalworldManifest:
        manifest = await info.context.app.palworld.create_manifest(
            steam_app_beta_branch=steam_app_beta_branch,
        )
        return PalworldManifest.construct_model(manifest)

    @strawberry.mutation
    async def start_palworld(
        self,
        path: str,
        info: Info[AppContext],
    ) -> PalworldInstance:
        container = await info.context.app.palworld.start(path)
        port = await info.context.app.docker.get_host_port(container)
        return PalworldInstance(
            path=path,
            container_name=info.context.app.palworld.get_container_name(path),
            running=True,
            port=port,
        )

    @strawberry.mutation
    async def stop_palworld(
        self,
        path: str,
        info: Info[AppContext],
    ) -> PalworldInstance:
        await info.context.app.palworld.stop(path)
        return PalworldInstance(
            path=path,
            container_name=info.context.app.palworld.get_container_name(path),
            running=False,
            port=None,
        )
