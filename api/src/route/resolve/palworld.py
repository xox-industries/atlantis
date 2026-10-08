from __future__ import annotations

import strawberry

from src.palworld import PersistedPalworldManifest


@strawberry.type
class PalworldManifest:
    _data: strawberry.Private[PersistedPalworldManifest]

    @staticmethod
    def construct_model(
        data: PersistedPalworldManifest,
        /,
    ) -> PalworldManifest:
        return PalworldManifest(_data=data)

    @strawberry.field
    def path(self) -> str:
        return self._data.path

    @strawberry.field
    def steam_app_beta_branch(self) -> str | None:
        return self._data.steam_app_beta_branch

    @strawberry.field
    def manifest_type(self) -> str:
        return self._data.manifest_type

    @strawberry.field
    def manifest_version(self) -> int:
        return self._data.manifest_version


@strawberry.type
class PalworldInstance:
    path: str
    container_name: str
    running: bool
    port: int | None = None
