from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.palworld import PalworldInstance, PalworldManifest


@strawberry.type
class DisplayPalworldType:
    @strawberry.field
    async def display_palworld(
        self,
        info: Info[AppContext],
    ) -> list[PalworldManifest]:
        manifests = await info.context.app.palworld.display_manifests()
        return [PalworldManifest.construct_model(manifest) for manifest in manifests]

    @strawberry.field
    async def display_palworld_instances(
        self,
        info: Info[AppContext],
    ) -> list[PalworldInstance]:
        manifests = await info.context.app.palworld.display_manifests()
        return [
            PalworldInstance(
                path=manifest.path,
                container_name=info.context.app.palworld.get_container_name(manifest.path),
                port=await info.context.app.palworld.get_host_port(manifest.path),
                running=await info.context.app.palworld.is_running(manifest.path),
            )
            for manifest in manifests
        ]
