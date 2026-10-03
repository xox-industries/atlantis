from __future__ import annotations

from typing import Any

import strawberry
from strawberry.types import Info

from src.route.context import AppContext
from src.route.resolve.terraria import TerrariaInstance, TerrariaManifest

UNSET = strawberry.UNSET


@strawberry.type
class MutationTerrariaType:
    @strawberry.mutation
    async def create_terraria(
        self,
        info: Info[AppContext],
        path: str,
        *,
        steam_app_beta_branch: str | None = None,
        game_autocreate: int,
        game_difficulty: int | None = None,
        game_motd: str | None = None,
        game_password: str | None = None,
        game_seed: str | None = None,
    ) -> TerrariaManifest:
        manifest = await info.context.app.terraria.create_manifest(
            path=path,
            steam_app_beta_branch=steam_app_beta_branch,
            game_autocreate=game_autocreate,
            game_difficulty=game_difficulty,
            game_motd=game_motd,
            game_password=game_password,
            game_seed=game_seed,
        )
        return TerrariaManifest.construct_model(manifest)

    @strawberry.mutation
    async def update_terraria(
        self,
        info: Info[AppContext],
        path: str,
        *,
        steam_app_beta_branch: str | None = UNSET,
        game_autocreate: int | None = UNSET,
        game_difficulty: int | None = UNSET,
        game_motd: str | None = UNSET,
        game_password: str | None = UNSET,
        game_seed: str | None = UNSET,
    ) -> TerrariaManifest:
        values: dict[str, Any] = {}
        if steam_app_beta_branch is not UNSET:
            values["steam_app_beta_branch"] = steam_app_beta_branch
        if game_autocreate is not UNSET:
            values["game_autocreate"] = game_autocreate
        if game_difficulty is not UNSET:
            values["game_difficulty"] = game_difficulty
        if game_motd is not UNSET:
            values["game_motd"] = game_motd
        if game_password is not UNSET:
            values["game_password"] = game_password
        if game_seed is not UNSET:
            values["game_seed"] = game_seed

        updated = await info.context.app.terraria.update_manifest(
            path,
            **values,
        )
        return TerrariaManifest.construct_model(updated)

    @strawberry.mutation
    async def start_terraria(
        self,
        path: str,
        info: Info[AppContext],
    ) -> TerrariaInstance:
        container = await info.context.app.terraria.start(path)
        port = await info.context.app.docker.get_host_port(container, protocol="tcp")
        return TerrariaInstance(
            path=path,
            container_name=info.context.app.terraria.get_container_name(path),
            running=True,
            port=port,
        )
