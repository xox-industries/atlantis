from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.valheim import ValheimInstance, ValheimManifest


@strawberry.type
class MutationValheimType:
    @strawberry.mutation
    async def create_valheim(
        self,
        info: Info[AppContext],
        *,
        steam_app_beta_branch: str | None = None,
    ) -> ValheimManifest:
        manifest = await info.context.app.valheim.create_manifest(
            steam_app_beta_branch=steam_app_beta_branch,
        )
        return ValheimManifest.construct_model(manifest)

    @strawberry.mutation
    async def start_valheim(
        self,
        path: str,
        info: Info[AppContext],
    ) -> ValheimInstance:
        container = await info.context.app.valheim.start(path)
        port = await info.context.app.docker.get_host_port(container)
        return ValheimInstance(
            path=path,
            container_name=info.context.app.valheim.get_container_name(path),
            running=True,
            port=port,
        )

    @strawberry.mutation
    async def stop_valheim(
        self,
        path: str,
        info: Info[AppContext],
    ) -> ValheimInstance:
        await info.context.app.valheim.stop(path)
        return ValheimInstance(
            path=path,
            container_name=info.context.app.valheim.get_container_name(path),
            running=False,
            port=None,
        )
