from __future__ import annotations

import asyncio
from pathlib import Path
from typing import TYPE_CHECKING, Literal

from fastapi import FastAPI

if TYPE_CHECKING:
    from asyncpg import Pool as PgPool
    from redis.asyncio import Redis
    from supabase import AClient as SupabaseClient

    from src.apt import Apt
    from src.docker import Docker
    from src.minecraft_java_edition import MinecraftJavaEdition
    from src.palworld import Palworld
    from src.persistence import Persistence
    from src.steam import Steam
    from src.terraria import Terraria


class App(FastAPI):
    _MOUNTINFO_MOUNT_POINT_INDEX = 4
    _MOUNTINFO_ROOT_INDEX = 3
    _MIN_MOUNTINFO_FIELDS = 5

    DATA_DIR = Path("/mnt/data")
    WINE_DIR = DATA_DIR.joinpath(".wine")

    env: Literal["production", "development"]
    supabase: SupabaseClient
    redis: Redis
    persistence: Persistence
    supabase_database_pool: PgPool

    apt: Apt
    docker: Docker
    steam: Steam

    minecraft_java_edition: MinecraftJavaEdition
    palworld: Palworld
    terraria: Terraria

    @classmethod
    def get_host_data_dir(cls) -> Path:
        mountinfo = Path("/proc/self/mountinfo")
        if mountinfo.exists():
            for line in mountinfo.read_text().splitlines():
                parts = line.split()
                if len(parts) >= cls._MIN_MOUNTINFO_FIELDS and parts[cls._MOUNTINFO_MOUNT_POINT_INDEX] == str(
                    cls.DATA_DIR,
                ):
                    root = (
                        parts[cls._MOUNTINFO_ROOT_INDEX]
                        .replace("\\040", " ")
                        .replace("\\011", "\t")
                        .replace("\\012", "\n")
                        .replace("\\\\", "\\")
                    )
                    return Path(root)

        return cls.DATA_DIR

    @classmethod
    def get_host_path(cls, path: Path) -> Path:
        path_str = str(path)
        data_dir_str = str(cls.DATA_DIR)
        if path_str.startswith(data_dir_str):
            relative = path_str[len(data_dir_str) :]
            return cls.get_host_data_dir().joinpath(relative.lstrip("/"))

        return path

    async def ensure_wineprefix(self) -> None:
        marker = self.WINE_DIR.joinpath(".updated")
        if marker.exists():
            return

        self.WINE_DIR.mkdir(parents=True, exist_ok=True)
        process = await asyncio.create_subprocess_exec(
            "bash",
            "-c",
            (
                f"export WINEPREFIX={self.WINE_DIR} && "
                "export WINEARCH=win64 && "
                "export WINEDEBUG=-all && "
                "xvfb-run -a winetricks -q --force vcrun2022"
            ),
        )
        await process.wait()
        marker.touch()
