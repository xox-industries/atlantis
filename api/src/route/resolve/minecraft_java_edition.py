from __future__ import annotations

import strawberry

from src.minecraft_java_edition import PersistedMinecraftJavaEditionManifest


@strawberry.type
class MinecraftJavaEditionModLoader:
    type: str
    version: str


@strawberry.type
class MinecraftJavaEditionManifest:
    _data: strawberry.Private[PersistedMinecraftJavaEditionManifest]

    @staticmethod
    def construct_model(
        data: PersistedMinecraftJavaEditionManifest,
        /,
    ) -> MinecraftJavaEditionManifest:
        return MinecraftJavaEditionManifest(_data=data)

    @strawberry.field
    def path(self) -> str:
        return self._data.path

    @strawberry.field
    def minecraft_version(self) -> str:
        return self._data.minecraft_version

    @strawberry.field
    def mod_loader(self) -> MinecraftJavaEditionModLoader:
        return MinecraftJavaEditionModLoader(
            type=self._data.modloader_type,
            version=self._data.modloader_version,
        )

    @strawberry.field
    def ram(self) -> int:
        return self._data.ram

    @strawberry.field
    def manifest_type(self) -> str:
        return self._data.manifest_type

    @strawberry.field
    def manifest_version(self) -> int:
        return self._data.manifest_version
