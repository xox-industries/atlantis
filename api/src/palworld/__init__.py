"""Palworld dedicated server lifecycle management."""

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


class Palworld(
    GameServer,
    SteamValidationMixin,
    DockerContainerStartMixin,
    SimpleStopMixin,
):
    DATA_DIR = App.DATA_DIR.joinpath("palworld")

    APP_DIR = Steam.APP_DIR.joinpath("PalServer")
    APP_SAVED_DIR = APP_DIR.joinpath("Pal", "Saved")
    APP_ID = "2394010"
    BASE_PORT = 8211
    GAME_KEY = "palworld"
    PROTOCOL = "udp"
    STEAM_ANONYMOUS = True
    STEAM_PLATFORM = "windows"

    CONTAINER_APP_DIR = Path("/home/app/PalServer")

    def _get_steam_beta_branch(self, _path: str | None, /) -> None:
        return None

    async def _ensure_instance_dirs(self, target_dir: Path, /) -> None:
        target_dir.joinpath("Saved").mkdir(parents=True, exist_ok=True)
        target_dir.joinpath("Mods").mkdir(parents=True, exist_ok=True)

    def _build_command(self, instance: str, /) -> list[str]:
        return [
            "bash",
            "-c",
            (
                f"[ -f {self.CONTAINER_APP_DIR.joinpath('PalServer.exe')} ] || ( "
                "echo 'Copying Palworld app into container' && "
                f"tar -C {self.APP_DIR} --exclude='Pal/Saved' -cf - . | "
                f"tar -C {self.CONTAINER_APP_DIR} -xf -"
                ") && "
                "echo 'Copying wineprefix' && "
                f"cp -a {self._app.WINE_DIR} /home/app/wineprefix && "
                "rm -f /home/app/wineprefix/wineserver /home/app/wineprefix/.update-timestamp && "
                "export WINEPREFIX=/home/app/wineprefix && "
                "export WINEARCH=win64 && "
                "export WINEDEBUG=-all && "
                f"echo 'Starting PalServer on port {self.BASE_PORT}' && "
                f"xvfb-run -a sh -c 'wineboot -u && "
                f"wine {self.CONTAINER_APP_DIR.joinpath('PalServer.exe')} "
                f"-publiclobby -port={self.BASE_PORT}'; exit $?"
            ),
        ]

    def _build_volumes(self, target_dir: Path, /) -> dict[str, str]:
        target_saved = target_dir.joinpath("Saved")
        target_mods = target_dir.joinpath("Mods")
        return {
            str(App.get_host_path(target_saved)): str(self.CONTAINER_APP_DIR.joinpath("Pal", "Saved")),
            str(App.get_host_path(target_mods)): str(self.CONTAINER_APP_DIR.joinpath("Mods")),
        }

    def _build_read_only_volumes(self) -> dict[str, str]:
        return {
            str(App.get_host_path(self.APP_DIR)): str(self.APP_DIR),
            str(App.get_host_path(self._app.WINE_DIR)): str(self._app.WINE_DIR),
        }
