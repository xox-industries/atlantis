from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from typing import Literal, cast

import vdf
from fastapi import HTTPException, status

from src.app import App


class Steam:
    DATA_DIR = App.DATA_DIR.joinpath(".steam")
    APP_DIR = DATA_DIR.joinpath(".local/share/Steam/steamapps/common")

    def __init__(self, app: App, /) -> None:
        self._app = app
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def account(self) -> str | None:
        config_file = self.DATA_DIR.joinpath(".local/share/Steam/config/config.vdf")
        if not config_file.exists():
            return None

        with config_file.open("r", encoding="utf-8") as f:
            data: dict = vdf.load(f)

        username = cast(
            "str",
            next(
                iter(
                    data["InstallConfigStore"]["Software"]["Valve"]["Steam"]["Accounts"],
                ),
            ),
        )
        username = username.strip()
        return username or None

    async def _commit(self, args: list[str], /) -> AsyncGenerator[str]:
        env = os.environ.copy()
        env["HOME"] = str(self.DATA_DIR)

        proc = await asyncio.create_subprocess_exec(
            *[
                "/usr/games/steamcmd",
                "+@ShutdownOnFailedCommand 1",
                "+@NoPromptForPassword 1",
                *args,
                "+quit",
            ],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.DATA_DIR,
            env=env,
        )

        if proc.stdout is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        async for raw in proc.stdout:
            line = raw.decode(errors="replace").rstrip("\r\n")
            if line:
                yield line

        await proc.wait()

        if proc.returncode != 0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def logout(self) -> None:
        config_path = self.DATA_DIR.joinpath(".local/share/Steam/config/config.vdf")
        await asyncio.to_thread(config_path.unlink, missing_ok=True)

    async def login(self, *, username: str, password: str, code: str | None = None) -> AsyncGenerator[str]:
        args = [
            "+login",
            username,
            password,
        ]
        if code:
            args.append(code)

        return self._commit(args)

    async def validate_app(
        self,
        *,
        app_id: str,
        anonymous: bool = False,
        platform: Literal["windows", "linux"] = "linux",
    ) -> AsyncGenerator[str]:
        args = [
            f'+@sSteamCmdForcePlatformType "{"windows" if platform == "windows" else "linux"}"',
            f"+login {'anonymous' if (anonymous or not self.account) else self.account}",
            f"+app_update {app_id}",
            "validate",
        ]

        return self._commit(args)
