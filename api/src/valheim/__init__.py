"""Valheim dedicated server lifecycle management."""

from __future__ import annotations

from pathlib import Path

from src.app import App
from src.game.base import GameServer
from src.game.mixins import (
    DockerContainerStartMixin,
    SimpleStopMixin,
    SteamValidationMixin,
)
from src.steam import Steam


class Valheim(
    GameServer,
    SteamValidationMixin,
    DockerContainerStartMixin,
    SimpleStopMixin,
):
    DATA_DIR = App.DATA_DIR.joinpath("valheim")

    APP_ID = "896660"
    BASE_PORT = 2456
    GAME_KEY = "valheim"
    PROTOCOL = "udp"
    STEAM_ANONYMOUS = True

    APP_NAME = "Valheim dedicated server"
    APP_DIR = Steam.APP_DIR.joinpath(APP_NAME)
    CONTAINER_APP_DIR = Path("/home/app").joinpath(APP_NAME)
    CONTAINER_CONFIG_DIR = Path("/home/app/.config/unity3d/IronGate/Valheim")
    CONTAINER_WORLDS_DIR = CONTAINER_CONFIG_DIR.joinpath("worlds_local")

    def _get_steam_beta_branch(self, _path: str | None, /) -> None:
        return None

    async def _ensure_instance_dirs(self, target_dir: Path, /) -> None:
        target_dir.joinpath("worlds_local").mkdir(parents=True, exist_ok=True)

    def _build_command(self, instance: str, /) -> list[str]:
        return [
            "bash",
            "-c",
            (
                f"[ -d '{self.CONTAINER_APP_DIR}' ] || ( "
                "echo 'Copying Valheim app into container' && "
                f"cp -a --reflink=auto '{self.APP_DIR}' '{self.CONTAINER_APP_DIR}' "
                ") && "
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

    def _build_volumes(self, target_dir: Path, /) -> dict[str, str]:
        return {str(App.get_host_path(target_dir)): str(self.CONTAINER_CONFIG_DIR)}
