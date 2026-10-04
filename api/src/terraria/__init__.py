from __future__ import annotations

import asyncio
import json
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TypedDict, Unpack

from aiodocker.containers import DockerContainer

from src.app import App
from src.game.base import ManifestGameServer
from src.game.error import (
    InstanceAlreadyRunningError,
    ManifestAlreadyExistsError,
    ManifestNotFoundError,
)
from src.steam import Steam
from src.terraria.model import PersistedTerrariaManifest


class Terraria(ManifestGameServer):
    DATA_DIR = App.DATA_DIR.joinpath("terraria")

    MANIFEST_FILE_NAME = "manifest.json"
    CONFIG_FILE_NAME = "manifest.conf"
    APP_ID = "105600"
    BASE_PORT = 7777
    GAME_KEY = "terraria"
    MAX_PLAYERS = 16
    PROTOCOL = "tcp"

    APP_DIR = Steam.APP_DIR.joinpath("Terraria")
    CONTAINER_APP_DIR = Path("/home/app/Terraria")
    CONTAINER_TERRARIA_DIR = Path("/home/app/.local/share/Terraria")
    CONTAINER_SAVED_DIR = CONTAINER_TERRARIA_DIR.joinpath("Worlds")
    CONTAINER_CONFIG_PATH = CONTAINER_TERRARIA_DIR.joinpath(CONFIG_FILE_NAME)
    CONTAINER_WORLD_PATH = CONTAINER_SAVED_DIR.joinpath("world.wld")

    def __init__(self, app: App, /) -> None:
        super().__init__(app)

    async def validate_app(self, path: str, /) -> AsyncGenerator[str]:
        target_dir = self.get_instance_dir(path)
        manifest = await asyncio.to_thread(
            self._read_sync,
            target_dir.joinpath(self.MANIFEST_FILE_NAME),
            self._relative_path(target_dir),
        )
        steam = self._app.steam
        return await steam.validate_app(
            app_id=self.APP_ID,
            anonymous=False,
            platform="linux",
            beta_branch=manifest.steam_app_beta_branch,
        )

    async def display_manifests(self) -> list[PersistedTerrariaManifest]:
        def _walk() -> list[PersistedTerrariaManifest]:
            manifests: list[PersistedTerrariaManifest] = []
            for manifest_path in sorted(self.DATA_DIR.rglob(self.MANIFEST_FILE_NAME)):
                relative_path = self._relative_path(manifest_path.parent)
                manifests.append(self._read_sync(manifest_path, relative_path))
            return manifests

        return await asyncio.to_thread(_walk)

    class CreateManifestArgs(TypedDict, total=False):
        steam_app_beta_branch: str | None
        game_autocreate: int
        game_difficulty: int | None
        game_motd: str | None
        game_password: str | None
        game_seed: str | None

    async def create_manifest(
        self,
        **kwargs: Unpack[CreateManifestArgs],
    ) -> PersistedTerrariaManifest:
        path = await self.create_instance()
        target_dir = self._resolve_path(path)
        manifest_path = target_dir.joinpath(self.MANIFEST_FILE_NAME)

        if manifest_path.exists():
            raise ManifestAlreadyExistsError(self._relative_path(target_dir))

        def _write() -> PersistedTerrariaManifest:
            target_dir.mkdir(parents=True, exist_ok=True)
            manifest = PersistedTerrariaManifest(
                path=self._relative_path(target_dir),
                steam_app_beta_branch=kwargs.get("steam_app_beta_branch"),
                game_autocreate=kwargs["game_autocreate"],
                game_difficulty=kwargs.get("game_difficulty"),
                game_motd=kwargs.get("game_motd"),
                game_password=kwargs.get("game_password"),
                game_seed=kwargs.get("game_seed"),
                game_npcstream=60,
                game_secure=False,
                game_upnp=True,
            )
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )
            return manifest

        return await asyncio.to_thread(_write)

    class UpdateManifestArgs(TypedDict, total=False):
        steam_app_beta_branch: str | None
        game_autocreate: int
        game_difficulty: int | None
        game_motd: str | None
        game_password: str | None
        game_seed: str | None

    async def update_manifest(
        self,
        path: str,
        /,
        **kwargs: Unpack[UpdateManifestArgs],
    ) -> PersistedTerrariaManifest:
        target_dir = self._resolve_path(path)
        manifest_path = target_dir.joinpath(self.MANIFEST_FILE_NAME)

        if not manifest_path.exists():
            raise ManifestNotFoundError(self._relative_path(target_dir))

        existing = await asyncio.to_thread(
            self._read_sync,
            manifest_path,
            self._relative_path(target_dir),
        )

        def _write() -> None:
            manifest = PersistedTerrariaManifest(
                path=self._relative_path(target_dir),
                steam_app_beta_branch=kwargs.get(
                    "steam_app_beta_branch",
                    existing.steam_app_beta_branch,
                ),
                game_autocreate=kwargs.get("game_autocreate", existing.game_autocreate),
                game_difficulty=kwargs.get("game_difficulty", existing.game_difficulty),
                game_motd=kwargs.get("game_motd", existing.game_motd),
                game_password=kwargs.get("game_password", existing.game_password),
                game_seed=kwargs.get("game_seed", existing.game_seed),
                game_npcstream=existing.game_npcstream,
                game_secure=existing.game_secure,
                game_upnp=existing.game_upnp,
            )
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )

        await asyncio.to_thread(_write)
        return await asyncio.to_thread(
            self._read_sync,
            manifest_path,
            self._relative_path(target_dir),
        )

    async def start(self, path: str, /) -> DockerContainer:
        target_dir = self.get_instance_dir(path)
        name = self.get_instance_name(path)

        if await self.is_running(path):
            raise InstanceAlreadyRunningError(path)

        await self._app.docker.stop(self.get_instance_name(path))

        manifest = await asyncio.to_thread(
            self._read_sync,
            target_dir.joinpath(self.MANIFEST_FILE_NAME),
            self._relative_path(target_dir),
        )
        await asyncio.to_thread(self._write_config, target_dir, manifest)

        image = os.environ["DOCKER_IMAGE"]

        command = [
            "bash",
            "-c",
            (
                f"rm -rf {self.CONTAINER_APP_DIR} && "
                "echo 'Copying Terraria app into container' && "
                f"cp -a --reflink=auto {self.APP_DIR} {self.CONTAINER_APP_DIR} && "
                f"chmod +x {self.CONTAINER_APP_DIR.joinpath('TerrariaServer.bin.x86_64')} && "
                f"mkdir -p {self.CONTAINER_SAVED_DIR} && "
                "echo 'Starting Terraria server' && "
                f"{self.CONTAINER_APP_DIR.joinpath('TerrariaServer.bin.x86_64')} "
                f"-config {self.CONTAINER_CONFIG_PATH}"
            ),
        ]

        volumes = {
            str(App.get_host_path(target_dir)): str(self.CONTAINER_TERRARIA_DIR),
        }
        read_only_volumes = {
            str(App.get_host_path(self.APP_DIR)): str(self.APP_DIR),
        }
        labels = {
            "atlantis.game": self.GAME_KEY,
            "atlantis.instance": path,
        }

        async with self._app.docker.find_free_port(
            base=self.BASE_PORT,
            game=self.GAME_KEY,
            protocol=self.PROTOCOL,
        ) as port:
            ports = {f"{self.BASE_PORT}/{self.PROTOCOL}": ("0.0.0.0", port)}
            return await self._app.docker.run(
                name=name,
                image=image,
                command=command,
                volumes=volumes,
                read_only_volumes=read_only_volumes,
                ports=ports,
                labels=labels,
            )

    async def stop(self, path: str, /) -> AsyncGenerator[str]:
        container = await self._app.docker.get_container(self.get_instance_name(path))
        if container is None:
            yield "Container not found"
            return

        info = await container.show()
        if not info.get("State", {}).get("Running", False):
            yield "Instance is not running"
            await container.delete(force=True)
            return

        stream = container.attach(stdin=True, stdout=True, stderr=True)
        try:
            yield "Attaching to container and sending stop command"
            command = b"exit\n"
            await stream.write_in(command)

            while True:
                msg = await stream.read_out()
                if msg is None:
                    break
                text = msg.data.decode("utf-8", errors="replace")
                if text:
                    yield text

            yield "Waiting for container to stop"
            await container.wait()
            yield "Container stopped"
        finally:
            await stream.close()
            await container.delete(force=True)

    def _write_config(
        self,
        target_dir: Path,
        manifest: PersistedTerrariaManifest,
        /,
    ) -> None:
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

    def _read_sync(
        self,
        manifest_path: Path,
        relative_path: str,
    ) -> PersistedTerrariaManifest:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        terraria = data["terraria"]
        return PersistedTerrariaManifest(
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
