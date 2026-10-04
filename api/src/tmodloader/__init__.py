"""TModLoader dedicated server lifecycle management."""

from __future__ import annotations

from pathlib import Path

from src.app import App
from src.game.terraria_like import (
    TerrariaLikeGameServer,
    build_new_manifest,
    build_updated_manifest,
    read_manifest,
)
from src.steam import Steam
from src.tmodloader.model import PersistedTModLoaderManifest


class TModLoader(TerrariaLikeGameServer[PersistedTModLoaderManifest]):
    DATA_DIR = App.DATA_DIR.joinpath("tmodloader")

    APP_ID = "1281930"
    GAME_KEY = "tmodloader"

    APP_DIR = Steam.APP_DIR.joinpath("tModLoader")
    CONTAINER_APP_DIR = Path("/home/app/tModLoader")

    def _build_command(self, _instance: str, /) -> list[str]:
        return [
            "bash",
            "-c",
            (
                f"[ -d {self.CONTAINER_APP_DIR} ] || ( "
                "echo 'Copying tModLoader app into container' && "
                f"cp -a --reflink=auto {self.APP_DIR} {self.CONTAINER_APP_DIR} "
                ") && "
                f"chmod +x {self.CONTAINER_APP_DIR.joinpath('start-tModLoaderServer.sh')} && "
                f"mkdir -p {self.CONTAINER_SAVED_DIR} && "
                "echo 'Starting tModLoader server' && "
                f"{self.CONTAINER_APP_DIR.joinpath('start-tModLoaderServer.sh')} "
                f"-config {self.CONTAINER_CONFIG_PATH} "
                f"-nosteam -tmlsavedirectory {self.CONTAINER_TERRARIA_DIR} "
                "-steamworkshopfolder none"
            ),
        ]

    def _read_sync(self, manifest_path: Path, relative_path: str, /) -> PersistedTModLoaderManifest:
        return read_manifest(PersistedTModLoaderManifest, manifest_path, relative_path)

    def _create_manifest_model(
        self,
        target_dir: Path,
        /,
        **kwargs: object,
    ) -> PersistedTModLoaderManifest:
        return build_new_manifest(
            PersistedTModLoaderManifest,
            path=self._relative_path(target_dir),
            values=kwargs,
        )

    def _update_manifest_model(
        self,
        target_dir: Path,
        existing: PersistedTModLoaderManifest,
        /,
        **kwargs: object,
    ) -> PersistedTModLoaderManifest:
        return build_updated_manifest(
            PersistedTModLoaderManifest,
            path=self._relative_path(target_dir),
            existing=existing,
            values=kwargs,
        )
