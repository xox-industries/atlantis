"""On-demand apt package installation for Atlantis game servers."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fastapi import HTTPException, status

if TYPE_CHECKING:
    from src.app import App


class Apt:
    """Installs apt packages on demand so services own their system dependencies.

    A process-wide lock serializes apt runs, and a local cache avoids repeatedly
    shelling out to ``dpkg`` for packages that were already installed this session.
    """

    _TAIL_LINES = 20

    def __init__(self, app: App, /) -> None:
        self._app = app
        self._lock = asyncio.Lock()
        self._installed: set[str] = set()

    async def _is_installed(self, package: str, /) -> bool:
        """Return whether ``package`` is already installed, updating the cache."""
        if package in self._installed:
            return True

        proc = await asyncio.create_subprocess_exec(
            "dpkg",
            "-s",
            package,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        if await proc.wait() != 0:
            return False

        self._installed.add(package)
        return True

    async def install(self, *packages: str) -> None:
        """Install the requested packages, skipping any that are already present."""
        async with self._lock:
            missing = [pkg for pkg in dict.fromkeys(packages) if not await self._is_installed(pkg)]
            if not missing:
                return

            await self._run_apt_get("update")
            await self._run_apt_get("install", "-y", "--no-install-recommends", *missing)
            self._installed.update(missing)

    async def _run_apt_get(self, *args: str) -> None:
        """Run ``sudo apt-get <args>`` and raise on failure with a tail of the output."""
        proc = await asyncio.create_subprocess_exec(
            "sudo",
            "apt-get",
            *args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        output, _ = await proc.communicate()
        if proc.returncode == 0:
            return

        text = output.decode(errors="replace") if output else ""
        tail = "\n".join(text.splitlines()[-self._TAIL_LINES :])
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"apt-get {' '.join(args)} failed:\n{tail}",
        )
