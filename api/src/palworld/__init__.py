from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path

from aiodocker.containers import DockerContainer

from src.app import App
from src.game.base import GameServer
from src.game.error import InstanceAlreadyRunningError
from src.steam import Steam


class Palworld(GameServer):
    DATA_DIR = App.DATA_DIR.joinpath("palworld")

    APP_DIR = Steam.APP_DIR.joinpath("PalServer")
    APP_SAVED_DIR = APP_DIR.joinpath("Pal", "Saved")
    APP_ID = "2394010"
    BASE_PORT = 8211
    GAME_KEY = "palworld"
    PROTOCOL = "udp"

    CONTAINER_APP_DIR = Path("/home/app/PalServer")

    def __init__(self, app: App, /) -> None:
        super().__init__(app)

    async def validate_app(self) -> AsyncGenerator[str]:
        steam = self._app.steam
        return await steam.validate_app(app_id=self.APP_ID, anonymous=True, platform="windows")

    def get_instance_saved_dir(self, name: str) -> Path:
        return self.get_instance_dir(name).joinpath("Saved")

    async def start(self, instance: str, /) -> DockerContainer:
        target = self.get_instance_dir(instance)

        if await self.is_running(instance):
            raise InstanceAlreadyRunningError(instance)

        await self.stop(instance)

        target_saved = self.get_instance_saved_dir(instance)
        target_saved.mkdir(parents=True, exist_ok=True)

        image = os.environ["DOCKER_IMAGE"]

        name = self.get_instance_name(instance)

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
                f"-publiclobby -port={self.BASE_PORT}"
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
            "atlantis.game": self.GAME_KEY,
            "atlantis.instance": instance,
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

    async def stop(self, instance: str, /) -> str:
        name = self.get_instance_name(instance)
        await self._app.docker.stop(name)
        return name
