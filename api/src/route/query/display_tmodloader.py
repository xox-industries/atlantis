from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.tmodloader import TModLoaderInstance, TModLoaderManifest


@strawberry.type
class DisplayTModLoaderType:
    @strawberry.field
    async def display_tmodloader(
        self,
        info: Info[AppContext],
    ) -> list[TModLoaderManifest]:
        manifests = await info.context.app.tmodloader.display_manifests()
        return [TModLoaderManifest.construct_model(manifest) for manifest in manifests]

    @strawberry.field
    async def display_tmodloader_instances(
        self,
        info: Info[AppContext],
    ) -> list[TModLoaderInstance]:
        manifests = await info.context.app.tmodloader.display_manifests()
        return [
            TModLoaderInstance(
                path=manifest.path,
                container_name=info.context.app.tmodloader.get_container_name(
                    manifest.path,
                ),
                port=await info.context.app.tmodloader.get_port(manifest.path),
                running=await info.context.app.tmodloader.is_running(manifest.path),
            )
            for manifest in manifests
        ]

    @strawberry.field
    async def display_tmodloader_directories(
        self,
        info: Info[AppContext],
    ) -> list[str]:
        return await info.context.app.tmodloader.display_directories()
