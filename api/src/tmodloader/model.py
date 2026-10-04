from __future__ import annotations

from src.terraria.model import PersistedTerrariaManifest


class PersistedTModLoaderManifest(PersistedTerrariaManifest):
    """TModLoader manifest; identical shape to Terraria, different ``manifestType``."""

    @property
    def manifest_type(self) -> str:
        return "tmodloader"
