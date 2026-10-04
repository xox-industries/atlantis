"""Terraria dedicated server lifecycle management."""

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
from src.terraria.model import PersistedTerrariaManifest


class Terraria(TerrariaLikeGameServer[PersistedTerrariaManifest]):
    DATA_DIR = App.DATA_DIR.joinpath("terraria")

    APP_ID = "105600"
    GAME_KEY = "terraria"

    APP_DIR = Steam.APP_DIR.joinpath("Terraria")
    CONTAINER_APP_DIR = Path("/home/app/Terraria")

    def _build_command(self, _instance: str, /) -> list[str]:
        return [
            "bash",
            "-c",
            (
                f"rm -rf {self.CONTAINER_APP_DIR} && "
                "echo 'Copying Terraria app into container' && "
                f"cp -a --reflink=auto {self.APP_DIR} {self.CONTAINER_APP_DIR} && "
                f"chmod +x {self.CONTAINER_APP_DIR.joinpath('TerrariaServer.bin.x86_64')} && "
                f"mkdir -p {self.CONTAINER_SAVED_DIR} && "
                "echo 'Starting Terraria server' && "
                f"{self.CONTAINER_APP_DIR.joinpath('TerrariaServer.bin.x86_64')} "
                f"-config {self.CONTAINER_CONFIG_PATH}"
            ),
        ]

    def _read_sync(self, manifest_path: Path, relative_path: str, /) -> PersistedTerrariaManifest:
        return read_manifest(PersistedTerrariaManifest, manifest_path, relative_path)

    def _create_manifest_model(
        self,
        target_dir: Path,
        /,
        **kwargs: object,
    ) -> PersistedTerrariaManifest:
        return build_new_manifest(
            PersistedTerrariaManifest,
            path=self._relative_path(target_dir),
            values=kwargs,
        )

    def _update_manifest_model(
        self,
        target_dir: Path,
        existing: PersistedTerrariaManifest,
        /,
        **kwargs: object,
    ) -> PersistedTerrariaManifest:
        return build_updated_manifest(
            PersistedTerrariaManifest,
            path=self._relative_path(target_dir),
            existing=existing,
            values=kwargs,
        )
