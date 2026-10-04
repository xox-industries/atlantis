from __future__ import annotations

from typing import Any

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.minecraft_java_edition import MinecraftJavaEditionManifest

UNSET = strawberry.UNSET


@strawberry.type
class MutationMinecraftJavaEditionType:
    @strawberry.mutation
    async def create_minecraft_java_edition(
        self,
        info: Info[AppContext],
        *,
        minecraft_version: str,
        modloader_type: str,
        modloader_version: str,
        ram: int,
    ) -> MinecraftJavaEditionManifest:
        manifest = await info.context.app.minecraft_java_edition.create_manifest(
            minecraft_version=minecraft_version,
            modloader_type=modloader_type,
            modloader_version=modloader_version,
            ram=ram,
        )
        return MinecraftJavaEditionManifest.construct_model(manifest)

    @strawberry.mutation
    async def update_minecraft_java_edition(
        self,
        info: Info[AppContext],
        path: str,
        *,
        minecraft_version: str | None = UNSET,
        modloader_type: str | None = UNSET,
        modloader_version: str | None = UNSET,
        ram: int | None = UNSET,
    ) -> MinecraftJavaEditionManifest:
        values: dict[str, Any] = {}
        if minecraft_version is not UNSET:
            values["minecraft_version"] = minecraft_version
        if modloader_type is not UNSET:
            values["modloader_type"] = modloader_type
        if modloader_version is not UNSET:
            values["modloader_version"] = modloader_version
        if ram is not UNSET:
            values["ram"] = ram

        lazy_manifest = await info.context.app.minecraft_java_edition.update_manifest(
            path,
            **values,
        )
        manifest = await lazy_manifest
        return MinecraftJavaEditionManifest.construct_model(manifest)
