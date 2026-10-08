from __future__ import annotations

import strawberry

from src.valheim import PersistedValheimManifest


@strawberry.type
class ValheimManifest:
    _data: strawberry.Private[PersistedValheimManifest]

    @staticmethod
    def construct_model(
        data: PersistedValheimManifest,
        /,
    ) -> ValheimManifest:
        return ValheimManifest(_data=data)

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
class ValheimInstance:
    path: str
    container_name: str
    port: int | None
    running: bool
