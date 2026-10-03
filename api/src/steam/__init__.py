"""SteamCMD integration for downloading and validating dedicated server apps."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import Literal

import vdf
from fastapi import HTTPException, status

from src.app import App


class Steam:
    """Async wrapper around SteamCMD for authenticating and installing apps.

    Steam data lives under ``App.DATA_DIR/.steam`` so the API container's HOME
    is not polluted. The wrapper reads the logged-in account from Steam's VDF
    config and falls back to anonymous downloads when no account is available.
    """

    DATA_DIR = App.DATA_DIR.joinpath(".steam")
    APP_DIR = DATA_DIR.joinpath(".local/share/Steam/steamapps/common")
    CONFIG_PATH = DATA_DIR.joinpath(".local/share/Steam/config/config.vdf")
    STEAMCMD = Path("/usr/games/steamcmd")

    def __init__(self, app: App, /) -> None:
        self._app = app
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    @property
    def account(self) -> str | None:
        """Return the first Steam account name stored in config.vdf, if any."""
        if not self.CONFIG_PATH.exists():
            return None

        with self.CONFIG_PATH.open("r", encoding="utf-8") as f:
            data: dict = vdf.load(f)

        accounts = (
            data.get("InstallConfigStore", {}).get("Software", {}).get("Valve", {}).get("Steam", {}).get("Accounts")
        )
        if not isinstance(accounts, dict) or not accounts:
            return None

        username = next(iter(accounts), "").strip()
        return username or None

    async def _commit(self, args: list[str], /) -> AsyncGenerator[str]:
        """Run SteamCMD with ``args`` and yield each line of stdout.

        Raises an HTTP 500 if SteamCMD exits non-zero.
        """
        env = os.environ.copy()
        env["HOME"] = str(self.DATA_DIR)

        proc = await asyncio.create_subprocess_exec(
            str(self.STEAMCMD),
            "+@ShutdownOnFailedCommand 1",
            "+@NoPromptForPassword 1",
            *args,
            "+quit",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=self.DATA_DIR,
            env=env,
        )

        if proc.stdout is None:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

        async for raw in proc.stdout:
            line = raw.decode(errors="replace").rstrip("\r\n")
            if line.strip():
                yield line

        await proc.wait()

        if proc.returncode != 0:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)

    async def logout(self) -> None:
        """Remove the stored Steam config, forcing the next operation to re-authenticate."""
        await asyncio.to_thread(self.CONFIG_PATH.unlink, missing_ok=True)

    async def login(
        self,
        *,
        username: str,
        password: str,
        code: str | None = None,
    ) -> AsyncGenerator[str]:
        """Log in to Steam with optional 2FA/Steam Guard ``code``."""
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
        beta_branch: str | None = None,
    ) -> AsyncGenerator[str]:
        """Download or validate ``app_id`` using SteamCMD.

        ``platform`` selects the forced platform type for Windows-only servers.
        ``beta_branch`` may be supplied to opt into a Steam app beta branch.
        """
        platform_arg = "windows" if platform == "windows" else "linux"
        account = "anonymous" if (anonymous or not self.account) else self.account

        args = [
            f'+@sSteamCmdForcePlatformType "{platform_arg}"',
            f"+login {account}",
            f"+app_update {app_id}{f' -beta {beta_branch}' if beta_branch else ''}",
            "validate",
        ]

        return self._commit(args)
