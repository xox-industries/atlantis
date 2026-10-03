from __future__ import annotations

import asyncio
import enum
import json
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TypedDict, Unpack

from src.app import App
from src.lib.path_utils import list_directories
from src.minecraft_java_edition.error import (
    InstanceAlreadyRunningError,
    InstanceNotFoundError,
    InvalidManifestPathError,
    ManifestAlreadyExistsError,
    ManifestNotFoundError,
)
from src.minecraft_java_edition.java_version import get_java_version
from src.minecraft_java_edition.model import PersistedMinecraftJavaEditionManifest
from src.minecraft_java_edition.server import build_server_command, prepare_server
from src.minecraft_java_edition.versions import (
    get_latest_minecraft_version,
    get_latest_modloader_version,
    validate_version,
)
from src.persistence.mixin.utils import LazyAwaitable


class ModLoaderType(enum.StrEnum):
    FORGE = "forge"
    FABRIC = "fabric"
    NEOFORGE = "neoforge"


class MinecraftJavaEdition:
    DATA_DIR = App.DATA_DIR.joinpath("minecraft-java-edition")

    MANIFEST_FILE_NAME = "manifest.json"
    BASE_PORT = 25565

    def __init__(self, app: App, /) -> None:
        self._app = app
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _resolve_path(self, path: str, /) -> Path:
        if not path:
            return self.DATA_DIR

        if path.startswith("/"):
            raise InvalidManifestPathError(path)

        resolved = self.DATA_DIR.joinpath(path).resolve()
        if not str(resolved).startswith(str(self.DATA_DIR.resolve())):
            raise InvalidManifestPathError(path)

        return resolved

    def _validate_modloader_type(self, modloader_type: str, /) -> None:
        if modloader_type not in {member.value for member in ModLoaderType}:
            msg = f"Modloader type must be one of: {', '.join(sorted(ModLoaderType))}"
            raise ValueError(msg)

    async def display_directories(self) -> list[str]:
        return await list_directories(self.DATA_DIR, max_depth=3)

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

    async def display_manifests(self) -> list[PersistedMinecraftJavaEditionManifest]:
        def _walk() -> list[PersistedMinecraftJavaEditionManifest]:
            manifests: list[PersistedMinecraftJavaEditionManifest] = []
            for manifest_path in sorted(self.DATA_DIR.rglob(self.MANIFEST_FILE_NAME)):
                relative_path = self._relative_path(manifest_path.parent)
                manifests.append(self._read_sync(manifest_path, relative_path))
            return manifests

        return await asyncio.to_thread(_walk)

    class CreateManifestArgs(TypedDict, total=False):
        path: str
        minecraft_version: str
        modloader_type: str
        modloader_version: str
        ram: int

    async def create_manifest(
        self,
        **kwargs: Unpack[CreateManifestArgs],
    ) -> PersistedMinecraftJavaEditionManifest:
        path = kwargs["path"]
        minecraft_version = kwargs["minecraft_version"]
        modloader_type = kwargs["modloader_type"]
        modloader_version = kwargs["modloader_version"]
        ram = kwargs["ram"]

        self._validate_modloader_type(modloader_type)
        target_dir = self._resolve_path(path)
        manifest_path = target_dir.joinpath(self.MANIFEST_FILE_NAME)

        if manifest_path.exists():
            raise ManifestAlreadyExistsError(self._relative_path(target_dir))

        java_version = get_java_version(minecraft_version)

        def _write() -> PersistedMinecraftJavaEditionManifest:
            target_dir.mkdir(parents=True, exist_ok=True)
            manifest = PersistedMinecraftJavaEditionManifest(
                path=self._relative_path(target_dir),
                minecraft_version=minecraft_version,
                modloader_type=modloader_type,
                modloader_version=modloader_version,
                ram=ram,
                java_version=java_version,
                jvm_arguments=[],
            )
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )
            return manifest

        return await asyncio.to_thread(_write)

    class UpdateManifestArgs(TypedDict, total=False):
        minecraft_version: str
        modloader_type: str
        modloader_version: str
        ram: int

    async def update_manifest(
        self,
        path: str,
        /,
        **kwargs: Unpack[UpdateManifestArgs],
    ) -> LazyAwaitable[PersistedMinecraftJavaEditionManifest]:
        target_dir = self._resolve_path(path)
        manifest_path = target_dir.joinpath(self.MANIFEST_FILE_NAME)

        if not manifest_path.exists():
            raise ManifestNotFoundError(self._relative_path(target_dir))

        existing = await asyncio.to_thread(
            self._read_sync,
            manifest_path,
            self._relative_path(target_dir),
        )

        minecraft_version = kwargs.get(
            "minecraft_version",
            existing.minecraft_version,
        )
        modloader_type = kwargs.get(
            "modloader_type",
            existing.modloader_type,
        )
        modloader_version = kwargs.get(
            "modloader_version",
            existing.modloader_version,
        )
        ram = kwargs.get("ram", existing.ram)
        java_version = (
            get_java_version(minecraft_version)
            if minecraft_version != existing.minecraft_version
            else existing.java_version
        )

        self._validate_modloader_type(modloader_type)

        def _write() -> None:
            manifest = PersistedMinecraftJavaEditionManifest(
                path=self._relative_path(target_dir),
                minecraft_version=minecraft_version,
                modloader_type=modloader_type,
                modloader_version=modloader_version,
                ram=ram,
                java_version=java_version,
                jvm_arguments=existing.jvm_arguments,
            )
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )

        await asyncio.to_thread(_write)

        async def _query() -> PersistedMinecraftJavaEditionManifest:
            return await asyncio.to_thread(
                self._read_sync,
                manifest_path,
                self._relative_path(target_dir),
            )

        return LazyAwaitable(_query())

    def _get_instance_name(self, path: str, /) -> str:
        return f"minecraft-java-edition-{path or 'default'}".lower().strip("/").replace("/", "-")

    def _get_instance_dir(self, path: str, /) -> Path:
        target_dir = self._resolve_path(path)
        if not target_dir.joinpath(self.MANIFEST_FILE_NAME).exists():
            raise InstanceNotFoundError(path)
        return target_dir

    async def start(self, path: str, /) -> AsyncGenerator[str]:
        target_dir = self._get_instance_dir(path)
        name = self._get_instance_name(path)

        if await self.is_running(path):
            raise InstanceAlreadyRunningError(path)

        await self._app.docker.stop(self._get_instance_name(path))

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
            "atlantis.game": "minecraft-java-edition",
            "atlantis.instance": path,
        }

        async with self._app.docker.find_free_port(
            base=self.BASE_PORT,
            game="minecraft-java-edition",
            protocol="tcp",
        ) as external_port:
            ports = {f"{self.BASE_PORT}/tcp": ("0.0.0.0", external_port)}  # noqa: S104
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

    def get_container_name(self, path: str, /) -> str:
        return self._app.docker.get_container_name(self._get_instance_name(path))

    async def stop(self, path: str, /) -> AsyncGenerator[str]:
        container = await self._app.docker.get_container(self._get_instance_name(path))
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
            command = b"stop\n"
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

    async def is_running(self, path: str, /) -> bool:
        name = self._get_instance_name(path)
        return await self._app.docker.is_running(name)

    async def get_port(self, path: str, /) -> int | None:
        name = self._get_instance_name(path)
        if not await self._app.docker.is_running(name):
            return None

        return await self._app.docker.get_host_port(name, protocol="tcp")

    def _relative_path(self, absolute_path: Path, /) -> str:
        relative = absolute_path.relative_to(self.DATA_DIR.resolve())
        return str(relative) if str(relative) != "." else ""

    def _read_sync(
        self,
        manifest_path: Path,
        relative_path: str,
    ) -> PersistedMinecraftJavaEditionManifest:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        minecraft = data["minecraft"]
        mod_loader = minecraft["modLoader"]
        minecraft_version = minecraft["version"]
        modloader_type = mod_loader["type"]
        modloader_version = mod_loader["version"]
        ram = minecraft["ram"]
        java_version = minecraft["javaVersion"]
        jvm_arguments = minecraft["jvmArguments"]
        return PersistedMinecraftJavaEditionManifest(
            path=relative_path,
            minecraft_version=minecraft_version,
            modloader_type=modloader_type,
            modloader_version=modloader_version,
            ram=ram,
            java_version=java_version,
            jvm_arguments=jvm_arguments,
        )
