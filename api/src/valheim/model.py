from __future__ import annotations

from pydantic import BaseModel, Field


class PersistedValheimManifest(BaseModel):
    path: str
    steam_app_beta_branch: str | None = Field(default=None)

    @property
    def manifest_type(self) -> str:
        return "valheim"

    @property
    def manifest_version(self) -> int:
        return 1

    def to_dict(self) -> dict:
        return {
            "valheim": {
                "steamAppBetaBranch": self.steam_app_beta_branch,
            },
            "manifestType": self.manifest_type,
            "manifestVersion": self.manifest_version,
        }
