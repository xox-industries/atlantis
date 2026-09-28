from __future__ import annotations

from pydantic import BaseModel


class PersistedMinecraftJavaEditionManifest(BaseModel):
    path: str
    minecraft_version: str
    modloader_type: str
    modloader_version: str
    ram: int

    @property
    def manifest_type(self) -> str:
        return "minecraft-java-edition"

    @property
    def manifest_version(self) -> int:
        return 1

    def to_dict(self) -> dict:
        return {
            "minecraft": {
                "version": self.minecraft_version,
                "modLoader": {
                    "type": self.modloader_type,
                    "version": self.modloader_version,
                },
                "ram": self.ram,
            },
            "manifestType": self.manifest_type,
            "manifestVersion": self.manifest_version,
        }
