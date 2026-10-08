"""Valheim dedicated server lifecycle management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import cast

from src.app import App
from src.game.manifest import ManifestGameServer
from src.game.mixins import (
    DockerContainerStartMixin,
    SimpleStopMixin,
    SteamValidationMixin,
)
from src.steam import Steam
from src.valheim.model import PersistedValheimManifest


class Valheim(
    ManifestGameServer[PersistedValheimManifest],
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

    def _read_sync(self, manifest_path: Path, relative_path: str, /) -> PersistedValheimManifest:
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        valheim = data["valheim"]
        return PersistedValheimManifest(
            path=relative_path,
            steam_app_beta_branch=valheim.get("steamAppBetaBranch"),
        )

    def _create_manifest_model(
        self,
        target_dir: Path,
        /,
        **kwargs: object,
    ) -> PersistedValheimManifest:
        return PersistedValheimManifest(
            path=self._relative_path(target_dir),
            steam_app_beta_branch=cast("str | None", kwargs.get("steam_app_beta_branch")),
        )

    def _update_manifest_model(
        self,
        target_dir: Path,
        existing: PersistedValheimManifest,
        /,
        **kwargs: object,
    ) -> PersistedValheimManifest:
        steam_app_beta_branch = kwargs.get("steam_app_beta_branch", existing.steam_app_beta_branch)
        return PersistedValheimManifest(
            path=self._relative_path(target_dir),
            steam_app_beta_branch=cast("str | None", steam_app_beta_branch),
        )

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
