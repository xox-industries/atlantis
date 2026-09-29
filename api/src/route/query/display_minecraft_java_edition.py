from __future__ import annotations

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.minecraft_java_edition import (
    MinecraftJavaEditionInstance,
    MinecraftJavaEditionManifest,
)


@strawberry.type
class DisplayMinecraftJavaEditionType:
    @strawberry.field
    async def display_minecraft_java_edition(
        self,
        info: Info[AppContext],
    ) -> list[MinecraftJavaEditionManifest]:
        manifests = await info.context.app.minecraft_java_edition.display_manifests()
        return [MinecraftJavaEditionManifest.construct_model(manifest) for manifest in manifests]

    @strawberry.field
    async def display_minecraft_java_edition_instances(
        self,
        info: Info[AppContext],
    ) -> list[MinecraftJavaEditionInstance]:
        manifests = await info.context.app.minecraft_java_edition.display_manifests()
        return [
            MinecraftJavaEditionInstance(
                path=manifest.path,
                container_name=info.context.app.minecraft_java_edition.get_container_name(
                    manifest.path,
                ),
                port=await info.context.app.minecraft_java_edition.get_port(manifest.path),
                running=await info.context.app.minecraft_java_edition.is_running(manifest.path),
            )
            for manifest in manifests
        ]

    @strawberry.field
    async def display_minecraft_java_edition_directories(
        self,
        info: Info[AppContext],
    ) -> list[str]:
        return await info.context.app.minecraft_java_edition.display_directories()

    @strawberry.field
    async def latest_minecraft_java_edition_minecraft_version(
        self,
        info: Info[AppContext],
    ) -> str:
        return await info.context.app.minecraft_java_edition.latest_minecraft_version()

    @strawberry.field
    async def latest_minecraft_java_edition_modloader_version(
        self,
        info: Info[AppContext],
        modloader_type: str,
        minecraft_version: str,
    ) -> str:
        return await info.context.app.minecraft_java_edition.latest_modloader_version(
            modloader_type,
            minecraft_version,
        )

    @strawberry.field
    async def validate_minecraft_java_edition_version(
        self,
        info: Info[AppContext],
        version_type: str,
        minecraft_version: str,
        modloader_version: str | None = None,
    ) -> bool:
        return await info.context.app.minecraft_java_edition.validate_version(
            version_type,
            minecraft_version,
            modloader_version,
        )
