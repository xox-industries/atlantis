"""Shared base and manifest builders for Terraria-like game servers."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel

from src.app import App
from src.game.manifest import ManifestGameServer
from src.game.mixins import (
    DockerContainerStartMixin,
    InteractiveStopMixin,
    SteamValidationMixin,
)

if TYPE_CHECKING:
    from src.terraria.model import PersistedTerrariaManifest


class CreateManifestArgs(BaseModel):
    """Validated arguments for creating a Terraria-like manifest."""

    steam_app_beta_branch: str | None = None
    game_autocreate: int
    game_difficulty: int | None = None
    game_motd: str | None = None
    game_password: str | None = None
    game_seed: str | None = None


class UpdateManifestArgs(BaseModel):
    """Validated arguments for updating a Terraria-like manifest.

    Every field is required: the update hook merges the existing manifest
    under the provided arguments before validation, so unspecified fields
    carry the persisted values.
    """

    steam_app_beta_branch: str | None
    game_autocreate: int
    game_difficulty: int | None
    game_motd: str | None
    game_password: str | None
    game_seed: str | None


def build_new_manifest[ManifestT: PersistedTerrariaManifest](
    model: type[ManifestT],
    *,
    path: str,
    values: dict[str, object],
) -> ManifestT:
    """Build a new manifest model from validated creation arguments."""
    args = CreateManifestArgs.model_validate(values)
    return model(
        path=path,
        steam_app_beta_branch=args.steam_app_beta_branch,
        game_autocreate=args.game_autocreate,
        game_difficulty=args.game_difficulty,
        game_motd=args.game_motd,
        game_password=args.game_password,
        game_seed=args.game_seed,
        game_npcstream=60,
        game_secure=False,
        game_upnp=True,
    )


def build_updated_manifest[ManifestT: PersistedTerrariaManifest](
    model: type[ManifestT],
    *,
    path: str,
    existing: PersistedTerrariaManifest,
    values: dict[str, object],
) -> ManifestT:
    """Build an updated manifest model by merging ``values`` over ``existing``."""
    args = UpdateManifestArgs.model_validate({**existing.model_dump(), **values})
    return model(
        path=path,
        steam_app_beta_branch=args.steam_app_beta_branch,
        game_autocreate=args.game_autocreate,
        game_difficulty=args.game_difficulty,
        game_motd=args.game_motd,
        game_password=args.game_password,
        game_seed=args.game_seed,
        game_npcstream=existing.game_npcstream,
        game_secure=existing.game_secure,
        game_upnp=existing.game_upnp,
    )


def read_manifest[ManifestT: PersistedTerrariaManifest](
    model: type[ManifestT],
    manifest_path: Path,
    relative_path: str,
) -> ManifestT:
    """Parse a persisted Terraria-like manifest JSON file into ``model``."""
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    terraria = data["terraria"]
    return model(
        path=relative_path,
        steam_app_beta_branch=terraria.get("steamAppBetaBranch"),
        game_autocreate=terraria["autocreate"],
        game_difficulty=terraria.get("difficulty"),
        game_motd=terraria.get("motd"),
        game_npcstream=terraria.get("npcstream"),
        game_password=terraria.get("password"),
        game_secure=terraria.get("secure"),
        game_seed=terraria.get("seed"),
        game_upnp=terraria.get("upnp"),
    )


class TerrariaLikeGameServer[ManifestT: PersistedTerrariaManifest](
    ManifestGameServer[ManifestT],
    SteamValidationMixin,
    DockerContainerStartMixin,
    InteractiveStopMixin,
):
    """Shared implementation for Terraria and TModLoader dedicated servers.

    Both games persist identically shaped manifests, write a Terraria-style
    server config, run inside a container with the same volume layout and stop
    via the ``exit`` console command. Subclasses supply class variables, the
    container ``_build_command`` and the three manifest hooks.
    """

    MANIFEST_FILE_NAME = "trident.manifest.json"
    CONFIG_FILE_NAME = "manifest.conf"
    BASE_PORT = 7777
    MAX_PLAYERS = 16
    PROTOCOL = "tcp"
    STOP_COMMAND = b"exit\n"
    STEAM_ANONYMOUS = False

    CONTAINER_TERRARIA_DIR = Path("/home/app/.local/share/Terraria")
    CONTAINER_SAVED_DIR = CONTAINER_TERRARIA_DIR.joinpath("Worlds")
    CONTAINER_CONFIG_PATH = CONTAINER_TERRARIA_DIR.joinpath(CONFIG_FILE_NAME)
    CONTAINER_WORLD_PATH = CONTAINER_SAVED_DIR.joinpath("world.wld")

    def _get_steam_beta_branch(self, path: str | None, /) -> str | None:
        if path is None:
            msg = "A manifest path is required to resolve the Steam beta branch"
            raise TypeError(msg)

        target_dir = self.get_instance_dir(path)
        manifest = self._read_sync(
            target_dir.joinpath(self.MANIFEST_FILE_NAME),
            self._relative_path(target_dir),
        )
        return manifest.steam_app_beta_branch

    async def _ensure_instance_dirs(self, target_dir: Path, /) -> None:
        manifest = await asyncio.to_thread(
            self._read_sync,
            target_dir.joinpath(self.MANIFEST_FILE_NAME),
            self._relative_path(target_dir),
        )
        await asyncio.to_thread(self._write_config, target_dir, manifest)

    def _build_volumes(self, target_dir: Path, /) -> dict[str, str]:
        return {str(App.get_host_path(target_dir)): str(self.CONTAINER_TERRARIA_DIR)}

    def _write_config(self, target_dir: Path, manifest: ManifestT, /) -> None:
        lines: list[str] = [
            f"world={self.CONTAINER_WORLD_PATH}",
            f"autocreate={manifest.game_autocreate}",
            "worldname=world",
            f"maxplayers={self.MAX_PLAYERS}",
            f"port={self.BASE_PORT}",
            f"secure={'1' if manifest.game_secure else '0'}",
            "language=en-US",
            f"upnp={'1' if manifest.game_upnp else '0'}",
            f"npcstream={manifest.game_npcstream}",
            "priority=0",
        ]

        if manifest.game_seed:
            lines.append(f"seed={manifest.game_seed}")
        if manifest.game_difficulty is not None:
            lines.append(f"difficulty={manifest.game_difficulty}")
        if manifest.game_password:
            lines.append(f"password={manifest.game_password}")
        if manifest.game_motd:
            lines.append(f"motd={manifest.game_motd}")

        target_dir.joinpath(self.CONFIG_FILE_NAME).write_text(
            "\n".join(lines) + "\n",
            encoding="utf-8",
        )
