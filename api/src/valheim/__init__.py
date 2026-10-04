from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path

from aiodocker.containers import DockerContainer

from src.app import App
from src.game.base import GameServer
from src.game.error import InstanceAlreadyRunningError
from src.steam import Steam


class Valheim(GameServer):
    DATA_DIR = App.DATA_DIR.joinpath("valheim")

    APP_ID = "896660"
    BASE_PORT = 2456
    GAME_KEY = "valheim"
    PROTOCOL = "udp"

    APP_NAME = "Valheim dedicated server"
    APP_DIR = Steam.APP_DIR.joinpath(APP_NAME)
    CONTAINER_APP_DIR = Path("/home/app").joinpath(APP_NAME)
    CONTAINER_CONFIG_DIR = Path("/home/app/.config/unity3d/IronGate/Valheim")
    CONTAINER_WORLDS_DIR = CONTAINER_CONFIG_DIR.joinpath("worlds_local")

    def __init__(self, app: App, /) -> None:
        super().__init__(app)

    async def validate_app(self) -> AsyncGenerator[str]:
        steam = self._app.steam
        return await steam.validate_app(
            app_id=self.APP_ID,
            anonymous=True,
            platform="linux",
        )

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

    async def stop(self, instance: str, /) -> None:
        name = self.get_instance_name(instance)
        await self._app.docker.stop(name)
