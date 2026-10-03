from __future__ import annotations

import strawberry

from src.terraria import PersistedTerrariaManifest


@strawberry.type
class TerrariaManifest:
    _data: strawberry.Private[PersistedTerrariaManifest]

    @staticmethod
    def construct_model(
        data: PersistedTerrariaManifest,
        /,
    ) -> TerrariaManifest:
        return TerrariaManifest(_data=data)

    @strawberry.field
    def path(self) -> str:
        return self._data.path

    @strawberry.field
    def steam_app_beta_branch(self) -> str | None:
        return self._data.steam_app_beta_branch

    @strawberry.field
    def game_autocreate(self) -> int:
        return self._data.game_autocreate

    @strawberry.field
    def game_difficulty(self) -> int | None:
        return self._data.game_difficulty

    @strawberry.field
    def game_motd(self) -> str | None:
        return self._data.game_motd

    @strawberry.field
    def game_npcstream(self) -> int | None:
        return self._data.game_npcstream

    @strawberry.field
    def game_password(self) -> str | None:
        return self._data.game_password

    @strawberry.field
    def game_secure(self) -> bool | None:
        return self._data.game_secure

    @strawberry.field
    def game_seed(self) -> str | None:
        return self._data.game_seed

    @strawberry.field
    def game_upnp(self) -> bool | None:
        return self._data.game_upnp

    @strawberry.field
    def manifest_type(self) -> str:
        return self._data.manifest_type

    @strawberry.field
    def manifest_version(self) -> int:
        return self._data.manifest_version


@strawberry.type
class TerrariaInstance:
    path: str
    container_name: str
    port: int | None
    running: bool
