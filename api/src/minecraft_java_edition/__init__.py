"""Minecraft Java Edition server manifest handling."""

from __future__ import annotations

import asyncio
import enum
import json
import os
from collections.abc import AsyncGenerator
from pathlib import Path

from src.app import App
from src.game.error import InstanceAlreadyRunningError
from src.game.manifest import ManifestGameServer
from src.game.mixins import InteractiveStopMixin
from src.minecraft_java_edition.java_version import get_java_version
from src.minecraft_java_edition.model import (
    CreateManifestArgs,
    PersistedMinecraftJavaEditionManifest,
    UpdateManifestArgs,
)
from src.minecraft_java_edition.server import build_server_command, prepare_server
from src.minecraft_java_edition.versions import (
    get_latest_minecraft_version,
    get_latest_modloader_version,
    validate_version,
)


class ModLoaderType(enum.StrEnum):
    FORGE = "forge"
    FABRIC = "fabric"
    NEOFORGE = "neoforge"


class MinecraftJavaEdition(
    ManifestGameServer[PersistedMinecraftJavaEditionManifest],
    InteractiveStopMixin,
):
    DATA_DIR = App.DATA_DIR.joinpath("minecraft-java-edition")

    MANIFEST_FILE_NAME = "manifest.json"
    BASE_PORT = 25565
    GAME_KEY = "minecraft-java-edition"
    PROTOCOL = "tcp"
    STOP_COMMAND = b"stop\n"

    def _validate_modloader_type(self, modloader_type: str, /) -> None:
        if modloader_type not in {member.value for member in ModLoaderType}:
            msg = f"Modloader type must be one of: {', '.join(sorted(ModLoaderType))}"
            raise ValueError(msg)

    async def latest_minecraft_version(self) -> str:
        return await get_latest_minecraft_version()

    async def latest_modloader_version(
        self,
        modloader_type: str,
        minecraft_version: str,
    ) -> str:
        return await get_latest_modloader_version(modloader_type, minecraft_version)

    async def validate_version(
        self,
        version_type: str,
        minecraft_version: str,
        modloader_version: str | None = None,
    ) -> bool:
        return await validate_version(version_type, minecraft_version, modloader_version)

    def _create_manifest_model(
        self,
        target_dir: Path,
        /,
        **kwargs: object,
    ) -> PersistedMinecraftJavaEditionManifest:
        args = CreateManifestArgs.model_validate(kwargs)
        self._validate_modloader_type(args.modloader_type)

        return PersistedMinecraftJavaEditionManifest(
            path=self._relative_path(target_dir),
            minecraft_version=args.minecraft_version,
            modloader_type=args.modloader_type,
            modloader_version=args.modloader_version,
            ram=args.ram,
            java_version=get_java_version(args.minecraft_version),
            jvm_arguments=[],
        )

    def _update_manifest_model(
        self,
        target_dir: Path,
        existing: PersistedMinecraftJavaEditionManifest,
        /,
        **kwargs: object,
    ) -> PersistedMinecraftJavaEditionManifest:
        args = UpdateManifestArgs.model_validate({**existing.model_dump(), **kwargs})
        self._validate_modloader_type(args.modloader_type)

        java_version = (
            get_java_version(args.minecraft_version)
            if args.minecraft_version != existing.minecraft_version
            else existing.java_version
        )

        return PersistedMinecraftJavaEditionManifest(
            path=self._relative_path(target_dir),
            minecraft_version=args.minecraft_version,
            modloader_type=args.modloader_type,
            modloader_version=args.modloader_version,
            ram=args.ram,
            java_version=java_version,
            jvm_arguments=existing.jvm_arguments,
        )

    async def start(self, path: str, /) -> AsyncGenerator[str]:
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

        async for line in prepare_server(target_dir, manifest):
            yield line

        command = build_server_command(target_dir, manifest)

        image = os.environ["DOCKER_IMAGE"]
        volumes = {
            str(self._app.get_host_path(target_dir)): str(target_dir),
        }
        labels = {
            "atlantis.game": self.GAME_KEY,
            "atlantis.instance": path,
        }

        async with self._app.docker.find_free_port(
            base=self.BASE_PORT,
            game=self.GAME_KEY,
            protocol=self.PROTOCOL,
        ) as external_port:
            ports = {f"{self.BASE_PORT}/{self.PROTOCOL}": ("0.0.0.0", external_port)}
            await self._app.docker.run(
                name=name,
                image=image,
                command=command,
                volumes=volumes,
                ports=ports,
                labels=labels,
                working_dir=str(target_dir),
            )
            yield f"Started on port {external_port}"

    def _read_sync(
        self,
        manifest_path: Path,
        relative_path: str,
        /,
    ) -> PersistedMinecraftJavaEditionManifest:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        minecraft = data["minecraft"]
        mod_loader = minecraft["modLoader"]
        return PersistedMinecraftJavaEditionManifest(
            path=relative_path,
            minecraft_version=minecraft["version"],
            modloader_type=mod_loader["type"],
            modloader_version=mod_loader["version"],
            ram=minecraft["ram"],
            java_version=minecraft["javaVersion"],
            jvm_arguments=minecraft["jvmArguments"],
        )
