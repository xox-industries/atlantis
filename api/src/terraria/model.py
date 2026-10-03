from __future__ import annotations

from pydantic import BaseModel, Field


class PersistedTerrariaManifest(BaseModel):
    path: str
    steam_app_beta_branch: str | None = Field(default=None)
    game_autocreate: int
    game_difficulty: int | None = Field(default=None)
    game_motd: str | None = Field(default=None)
    game_npcstream: int | None = Field(default=None)
    game_password: str | None = Field(default=None)
    game_secure: bool | None = Field(default=None)
    game_seed: str | None = Field(default=None)
    game_upnp: bool | None = Field(default=None)

    @property
    def manifest_type(self) -> str:
        return "terraria"

    @property
    def manifest_version(self) -> int:
        return 1

    def to_dict(self) -> dict:
        return {
            "terraria": {
                "steamAppBetaBranch": self.steam_app_beta_branch,
                "autocreate": self.game_autocreate,
                "difficulty": self.game_difficulty,
                "motd": self.game_motd,
                "npcstream": self.game_npcstream,
                "password": self.game_password,
                "secure": self.game_secure,
                "seed": self.game_seed,
                "upnp": self.game_upnp,
            },
            "manifestType": self.manifest_type,
            "manifestVersion": self.manifest_version,
        }
