from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.valheim import ValheimInstance, ValheimManifest


@strawberry.type
class DisplayValheimType:
    @strawberry.field
    async def display_valheim(
        self,
        info: Info[AppContext],
    ) -> list[ValheimManifest]:
        manifests = await info.context.app.valheim.display_manifests()
        return [ValheimManifest.construct_model(manifest) for manifest in manifests]

    @strawberry.field
    async def display_valheim_instances(
        self,
        info: Info[AppContext],
    ) -> list[ValheimInstance]:
        manifests = await info.context.app.valheim.display_manifests()
        return [
            ValheimInstance(
                path=manifest.path,
                container_name=info.context.app.valheim.get_container_name(manifest.path),
                port=await info.context.app.valheim.get_host_port(manifest.path),
                running=await info.context.app.valheim.is_running(manifest.path),
            )
            for manifest in manifests
        ]
