from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from pathlib import Path

from aiodocker.containers import DockerContainer

from src.app import App
from src.steam import Steam


class InstanceNotFoundError(ValueError):
    """Raised when the requested instance does not exist."""

    def __init__(self, instance: str) -> None:
        super().__init__(f"Instance {instance!r} does not exist")


class InstanceAlreadyRunningError(RuntimeError):
    """Raised when the requested instance is already running."""

    def __init__(self, instance: str) -> None:
        super().__init__(f"Instance {instance!r} is already running")


class InstanceNotRunningError(RuntimeError):
    """Raised when the requested instance is not running."""

    def __init__(self, instance: str) -> None:
        super().__init__(f"Instance {instance!r} is not running")


class Valheim:
    DATA_DIR = App.DATA_DIR.joinpath("valheim")

    APP_ID = "896660"
    BASE_PORT = 2456

    APP_NAME = "Valheim dedicated server"
    APP_DIR = Steam.APP_DIR.joinpath(APP_NAME)
    CONTAINER_APP_DIR = Path("/home/app").joinpath(APP_NAME)
    CONTAINER_CONFIG_DIR = Path("/home/app/.config/unity3d/IronGate/Valheim")
    CONTAINER_WORLDS_DIR = CONTAINER_CONFIG_DIR.joinpath("worlds_local")

    def __init__(self, app: App, /) -> None:
        self._app = app
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    async def validate_app(self) -> AsyncGenerator[str]:
        steam = self._app.steam
        return await steam.validate_app(
            app_id=self.APP_ID,
            anonymous=True,
            platform="linux",
        )

    async def ls(self) -> list[str]:
        return [path.name for path in self.DATA_DIR.iterdir() if path.is_dir()]

    async def touch(self) -> str:
        name = f"ses_{datetime.now(tz=UTC).strftime('%Y%m%d%H%M%S')}"
        self.DATA_DIR.joinpath(name).mkdir(exist_ok=True)
        return name

    def get_instance_dir(self, name: str) -> Path:
        instance = self.DATA_DIR.joinpath(name)
        if not instance.is_dir():
            raise InstanceNotFoundError(name)

        return instance

    def get_instance_name(self, instance: str) -> str:
        return f"valheim-{instance}".lower().strip()

    def get_container_name(self, instance: str, /) -> str:
        return self._app.docker.get_container_name(self.get_instance_name(instance))

    async def start(self, instance: str, /) -> DockerContainer:
        target = self.get_instance_dir(instance)

        if await self.is_running(instance):
            raise InstanceAlreadyRunningError(instance)

        await self.stop(instance)

        target_worlds = target.joinpath("worlds_local")
        target_worlds.mkdir(parents=True, exist_ok=True)

        image = os.environ["DOCKER_IMAGE"]
        name = self.get_instance_name(instance)

        command = [
            "bash",
            "-c",
            (
                f"rm -rf '{self.CONTAINER_APP_DIR}' && "
                "echo 'Copying Valheim app into container' && "
                f"cp -a --reflink=auto '{self.APP_DIR}' '{self.CONTAINER_APP_DIR}' && "
                f"chmod +x '{self.CONTAINER_APP_DIR.joinpath('valheim_server.x86_64')}' && "
                f"mkdir -p '{self.CONTAINER_WORLDS_DIR}' && "
                "echo 'Starting Valheim server' && "
                f"export LD_LIBRARY_PATH='{self.CONTAINER_APP_DIR.joinpath('linux64')}':\"$LD_LIBRARY_PATH\" && "
                "export SteamAppId=892970 && "
                f"'{self.CONTAINER_APP_DIR.joinpath('valheim_server.x86_64')}' "
                f"-name '{instance}' "
                f"-port {self.BASE_PORT} "
                "-public 0 "
                "-nographics "
                "-batchmode "
                "-crossplay"
            ),
        ]

        volumes = {
            str(App.get_host_path(target)): str(self.CONTAINER_CONFIG_DIR),
        }
        read_only_volumes = {
            str(App.get_host_path(self.APP_DIR)): str(self.APP_DIR),
        }
        labels = {
            "atlantis.game": "valheim",
            "atlantis.instance": instance,
        }

        async with self._app.docker.find_free_port(
            base=self.BASE_PORT,
            game="valheim",
            protocol="udp",
        ) as port:
            ports = {f"{self.BASE_PORT}/udp": ("0.0.0.0", port)}  # noqa: S104
            return await self._app.docker.run(
                name=name,
                image=image,
                command=command,
                volumes=volumes,
                read_only_volumes=read_only_volumes,
                ports=ports,
                labels=labels,
            )

    async def stop(self, instance: str, /) -> None:
        name = self.get_instance_name(instance)
        await self._app.docker.stop(name)

    async def is_running(self, instance: str, /) -> bool:
        return await self._app.docker.is_running(self.get_instance_name(instance))

    async def get_port(self, instance: str, /) -> int | None:
        name = self.get_instance_name(instance)
        if not await self._app.docker.is_running(name):
            return None

        return await self._app.docker.get_host_port(name, protocol="udp")
