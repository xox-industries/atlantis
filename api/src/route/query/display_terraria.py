from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.terraria import TerrariaInstance, TerrariaManifest


@strawberry.type
class DisplayTerrariaType:
    @strawberry.field
    async def display_terraria(
        self,
        info: Info[AppContext],
    ) -> list[TerrariaManifest]:
        manifests = await info.context.app.terraria.display_manifests()
        return [TerrariaManifest.construct_model(manifest) for manifest in manifests]

    @strawberry.field
    async def display_terraria_instances(
        self,
        info: Info[AppContext],
    ) -> list[TerrariaInstance]:
        manifests = await info.context.app.terraria.display_manifests()
        return [
            TerrariaInstance(
                path=manifest.path,
                container_name=info.context.app.terraria.get_container_name(manifest.path),
                port=await info.context.app.terraria.get_port(manifest.path),
                running=await info.context.app.terraria.is_running(manifest.path),
            )
            for manifest in manifests
        ]
