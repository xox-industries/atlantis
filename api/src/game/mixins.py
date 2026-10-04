"""Reusable behavior mixins for Atlantis game server implementations."""

from __future__ import annotations

import asyncio
import os
from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import ClassVar, Literal

from aiodocker.containers import DockerContainer

from src.app import App
from src.game.error import InstanceAlreadyRunningError


class SteamValidationMixin(ABC):
    """Validates the game's Steam app with SteamCMD before starting."""

    APP_ID: ClassVar[str]
    """Steam app id validated by :meth:`validate_app`."""

    STEAM_ANONYMOUS: ClassVar[bool] = False
    """Whether to validate with the anonymous Steam account."""

    STEAM_PLATFORM: ClassVar[Literal["windows", "linux"]] = "linux"
    """Steam platform type to force during validation."""

    _app: App

    @abstractmethod
    def _get_steam_beta_branch(self, path: str | None, /) -> str | None:
        """Return the Steam beta branch to validate, or ``None``.

        Args:
            path: Instance path, or ``None`` for games without manifests.

        """

    async def validate_app(self, path: str | None = None, /) -> AsyncGenerator[str]:
        """Validate the Steam app, yielding each SteamCMD output line.

        Args:
            path: Instance path used to resolve the beta branch, if any.

        """
        beta_branch = await asyncio.to_thread(self._get_steam_beta_branch, path)
        return await self._app.steam.validate_app(
            app_id=self.APP_ID,
            anonymous=self.STEAM_ANONYMOUS,
            platform=self.STEAM_PLATFORM,
            beta_branch=beta_branch,
        )


class DockerContainerStartMixin(ABC):
    """Starts a game instance as a sibling Docker container."""

    BASE_PORT: ClassVar[int]
    GAME_KEY: ClassVar[str]
    PROTOCOL: ClassVar[str]
    APP_DIR: ClassVar[Path]

    _app: App

    async def start(self, instance: str, /) -> DockerContainer:
        """Start the instance's container and return it.

        Args:
            instance: Instance name or relative path.

        Raises:
            InstanceAlreadyRunningError: If the instance is already running.

        """
        target_dir = self.get_instance_dir(instance)

        if await self.is_running(instance):
            raise InstanceAlreadyRunningError(instance)

        await self._app.docker.stop(self.get_instance_name(instance))
        await self._ensure_instance_dirs(target_dir)

        image = os.environ["DOCKER_IMAGE"]
        name = self.get_instance_name(instance)
        command = self._build_command(instance)
        volumes = self._build_volumes(target_dir)
        read_only_volumes = self._build_read_only_volumes()

        async with self._app.docker.find_free_port(
            base=self.BASE_PORT,
            game=self.GAME_KEY,
            protocol=self.PROTOCOL,
        ) as port:
            return await self._app.docker.run(
                name=name,
                image=image,
                command=command,
                volumes=volumes,
                read_only_volumes=read_only_volumes,
                ports=self._build_ports(port),
                labels=self._build_labels(instance),
            )

    @abstractmethod
    def _build_command(self, instance: str, /) -> list[str]:
        """Build the shell command executed inside the container.

        Args:
            instance: Instance name or relative path.

        """

    @abstractmethod
    async def _ensure_instance_dirs(self, target_dir: Path, /) -> None:
        """Prepare the instance directory before the container starts.

        Args:
            target_dir: Absolute instance directory.

        """

    def _build_volumes(self, target_dir: Path, /) -> dict[str, str]:
        """Map writable host paths to their container counterparts.

        Args:
            target_dir: Absolute instance directory.

        """
        return {str(App.get_host_path(target_dir)): str(target_dir)}

    def _build_read_only_volumes(self) -> dict[str, str]:
        """Map read-only host paths (game app data) into the container."""
        return {str(App.get_host_path(self.APP_DIR)): str(self.APP_DIR)}

    def _build_ports(self, port: int, /) -> dict[str, tuple[str, int]]:
        """Map the container game port to the allocated host ``port``."""
        return {f"{self.BASE_PORT}/{self.PROTOCOL}": ("0.0.0.0", port)}

    def _build_labels(self, instance: str, /) -> dict[str, str]:
        """Return Docker labels identifying the game and instance."""
        return {
            "atlantis.game": self.GAME_KEY,
            "atlantis.instance": instance,
        }

    # Redeclared so the mixin body typechecks against the GameServer contract.
    @abstractmethod
    def get_instance_dir(self, instance: str, /) -> Path: ...

    @abstractmethod
    async def is_running(self, instance: str, /) -> bool: ...

    @abstractmethod
    def get_instance_name(self, instance: str, /) -> str: ...


class InteractiveStopMixin(ABC):
    """Stops a running instance by writing a command to its console stream."""

    STOP_COMMAND: ClassVar[bytes]
    """Command bytes written to the container console to request shutdown."""

    _app: App

    async def stop(self, path: str, /) -> AsyncGenerator[str]:
        """Attach to the running container, send ``STOP_COMMAND`` and stream output.

        Args:
            path: Instance name or relative path.

        """
        container = await self._app.docker.get_container(self.get_instance_name(path))
        if container is None:
            yield "Container not found"
            return

        info = await container.show()
        if not info.get("State", {}).get("Running", False):
            yield "Instance is not running"
            await container.delete(force=True)
            return

        stream = container.attach(stdin=True, stdout=True, stderr=True)
        try:
            yield "Attaching to container and sending stop command"
            await stream.write_in(self.STOP_COMMAND)

            while True:
                msg = await stream.read_out()
                if msg is None:
                    break
                text = msg.data.decode("utf-8", errors="replace")
                if text:
                    yield text

            yield "Waiting for container to stop"
            await container.wait()
            yield "Container stopped"
        finally:
            await stream.close()
            await container.delete(force=True)

    # Redeclared so the mixin body typechecks against the GameServer contract.
    @abstractmethod
    def get_instance_name(self, instance: str, /) -> str: ...


class SimpleStopMixin(ABC):
    """Stops a running instance by stopping and removing its container."""

    _app: App

    async def stop(self, instance: str, /) -> None:
        """Stop and remove the instance's container.

        Args:
            instance: Instance name or relative path.

        """
        await self._app.docker.stop(self.get_instance_name(instance))

    # Redeclared so the mixin body typechecks against the GameServer contract.
    @abstractmethod
    def get_instance_name(self, instance: str, /) -> str: ...
