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


_HTTP_INTERNAL_SERVER_ERROR = 500


class Palworld:
    DATA_DIR = App.DATA_DIR.joinpath("palworld")

    APP_DIR = Steam.APP_DIR.joinpath("PalServer")
    APP_SAVED_DIR = APP_DIR.joinpath("Pal", "Saved")
    APP_ID = "2394010"
    BASE_PORT = 8211

    CONTAINER_APP_DIR = Path("/home/app/PalServer")

    def __init__(self, app: App, /) -> None:
        self._app = app
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    async def validate_app(self) -> AsyncGenerator[str]:
        steam = self._app.steam
        return await steam.validate_app(app_id=self.APP_ID, anonymous=True, platform="windows")

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

    def get_instance_saved_dir(self, name: str) -> Path:
        return self.get_instance_dir(name).joinpath("Saved")

    def get_instance_name(self, instance: str) -> str:
        return f"{self.__class__.__name__}-{instance}".lower().strip()

    async def start(self, instance: str, /) -> DockerContainer:
        target = self.get_instance_dir(instance)

        if await self.is_running(instance):
            raise InstanceAlreadyRunningError(instance)

        await self.stop(instance)

        target_saved = self.get_instance_saved_dir(instance)
        target_saved.mkdir(parents=True, exist_ok=True)

        image = os.environ["DOCKER_IMAGE"]

        name = self.get_instance_name(instance)
        server_log = target.joinpath("server.log")

        command = [
            "bash",
            "-c",
            (
                f"rm -rf {self.CONTAINER_APP_DIR} && "
                "echo 'Copying app into container' && "
                f"cp -a --reflink=auto {self.APP_DIR} {self.CONTAINER_APP_DIR} && "
                f"rm -rf {self.CONTAINER_APP_DIR.joinpath('Pal', 'Saved')} && "
                f"ln -s {target_saved!s} {self.CONTAINER_APP_DIR.joinpath('Pal', 'Saved')} && "
                "echo 'Copying wineprefix' && "
                f"cp -a {self._app.WINE_DIR} /home/app/wineprefix && "
                "rm -f /home/app/wineprefix/wineserver /home/app/wineprefix/.update-timestamp && "
                f"export WINEPREFIX=/home/app/wineprefix && "
                "export WINEARCH=win64 && "
                "export WINEDEBUG=-all && "
                "echo 'Booting wineprefix' && "
                "xvfb-run -a wineboot -u && "
                f"echo 'Starting PalServer on port {self.BASE_PORT}' && "
                f"xvfb-run -a wine {self.CONTAINER_APP_DIR.joinpath('PalServer.exe')} "
                f"-publiclobby -port={self.BASE_PORT} "
                f"> {server_log} 2>&1"
            ),
        ]

        volumes = {
            str(App.get_host_path(target)): str(target),
            str(App.get_host_path(target_saved)): str(target_saved),
        }
        read_only_volumes = {
            str(App.get_host_path(self.APP_DIR)): str(self.APP_DIR),
            str(App.get_host_path(self._app.WINE_DIR)): str(self._app.WINE_DIR),
        }
        labels = {
            "atlantis.game": "palworld",
            "atlantis.instance": instance,
        }

        async with self._app.docker.find_free_port(
            base=self.BASE_PORT,
            game="palworld",
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

    async def stop(self, instance: str, /) -> str:
        name = self.get_instance_name(instance)
        await self._app.docker.stop(name)
        return name

    async def is_running(self, instance: str, /) -> bool:
        return await self._app.docker.is_running(self.get_instance_name(instance))

    async def get_port(self, instance: str, /) -> int | None:
        name = self.get_instance_name(instance)
        if not await self._app.docker.is_running(name):
            return None

        return await self._app.docker.get_host_port(name, protocol="udp")
