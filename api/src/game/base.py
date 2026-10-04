from __future__ import annotations

import asyncio
from abc import ABC
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar

from src.game.error import InstanceNotFoundError, InvalidManifestPathError

if TYPE_CHECKING:
    from src.app import App


class GameServer(ABC):
    """Abstract base class shared by all Atlantis game server implementations.

    Subclasses declare their data directory, base port, network protocol and a
    short game key. The base class then provides common instance lifecycle
    helpers such as listing instances, creating timestamped instance
    directories, computing Docker container names and querying the host port.
    """

    DATA_DIR: ClassVar[Path]
    """Root directory where this game's instance folders are stored."""

    BASE_PORT: ClassVar[int]
    """Default container port used by this game."""

    PROTOCOL: ClassVar[str] = "tcp"
    """Transport protocol used for the game's main port (``tcp`` or ``udp``)."""

    GAME_KEY: ClassVar[str]
    """Short identifier used in container names and labels, e.g. ``palworld``."""

    def __init__(self, app: App, /) -> None:
        """Initialize the game server and ensure its data directory exists.

        Args:
            app: The shared Atlantis application container.

        """
        self._app = app
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)

    async def list_instances(self) -> list[str]:
        """Return the names of every instance directory under ``DATA_DIR``.

        The directory walk is executed in a thread to avoid blocking the event
        loop on slow filesystem operations.

        Returns:
            Sorted list of instance directory names.

        """

        def _walk() -> list[str]:
            return sorted(path.name for path in self.DATA_DIR.iterdir() if path.is_dir())

        return await asyncio.to_thread(_walk)

    async def create_instance(self) -> str:
        """Create a new instance directory with a timestamped name.

        The generated name follows the ``ses_YYYYMMDDhhmmss`` convention used
        across all Atlantis game servers.

        Returns:
            The name of the newly created instance directory.

        """
        name = f"ses_{datetime.now(tz=UTC).strftime('%Y%m%d%H%M%S')}"
        self.DATA_DIR.joinpath(name).mkdir(exist_ok=True)
        return name

    def get_instance_name(self, instance: str, /) -> str:
        """Return the Docker container name for an instance.

        The name is derived from :attr:`GAME_KEY` and the instance identifier,
        normalized to lower case with slashes replaced by dashes.

        Args:
            instance: Instance name or relative path.

        Returns:
            Container-safe name such as ``palworld-myinstance``.

        """
        return f"{self.GAME_KEY}-{instance or 'default'}".lower().strip("/").replace("/", "-")

    def get_instance_dir(self, name: str, /) -> Path:
        """Resolve and validate that an instance directory exists.

        Args:
            name: Name of the instance directory.

        Returns:
            Absolute path to the instance directory.

        Raises:
            InstanceNotFoundError: If the directory does not exist.

        """
        instance = self.DATA_DIR.joinpath(name)
        if not instance.is_dir():
            raise InstanceNotFoundError(name)
        return instance

    def get_container_name(self, instance: str, /) -> str:
        """Return the fully qualified Docker container name for an instance.

        Args:
            instance: Instance name or relative path.

        Returns:
            Docker container name as registered with the daemon.

        """
        return self._app.docker.get_container_name(self.get_instance_name(instance))

    async def is_running(self, instance: str, /) -> bool:
        """Return whether the instance's container is currently running.

        Args:
            instance: Instance name or relative path.

        """
        return await self._app.docker.is_running(self.get_instance_name(instance))

    async def get_host_port(self, instance: str, /) -> int | None:
        """Return the host-bound port for a running instance.

        Args:
            instance: Instance name or relative path.

        Returns:
            The host port mapped to :attr:`BASE_PORT`, or ``None`` when the
            instance is not running.

        """
        name = self.get_instance_name(instance)
        if not await self._app.docker.is_running(name):
            return None

        return await self._app.docker.get_host_port(name, protocol=self.PROTOCOL)


class ManifestGameServer(GameServer, ABC):
    """Base class for game servers that persist per-instance manifests.

    In addition to the helpers provided by :class:`GameServer`, this class
    adds safe path resolution and relative-path conversion for manifest files
    stored inside each instance directory.
    """

    MANIFEST_FILE_NAME: ClassVar[str] = "manifest.json"
    """Filename used for the per-instance manifest."""

    def _resolve_path(self, path: str, /) -> Path:
        """Resolve a relative instance path to an absolute path under ``DATA_DIR``.

        Empty paths resolve to :attr:`DATA_DIR` itself. Absolute paths and
        paths that escape ``DATA_DIR`` are rejected.

        Args:
            path: Relative instance path, possibly empty.

        Returns:
            Absolute, resolved path within ``DATA_DIR``.

        Raises:
            InvalidManifestPathError: If the path is absolute or escapes
                ``DATA_DIR``.

        """
        if not path:
            return self.DATA_DIR

        if path.startswith("/"):
            raise InvalidManifestPathError(path)

        resolved = self.DATA_DIR.joinpath(path).resolve()
        if not str(resolved).startswith(str(self.DATA_DIR.resolve())):
            raise InvalidManifestPathError(path)

        return resolved

    def _relative_path(self, absolute_path: Path, /) -> str:
        """Return the path of ``absolute_path`` relative to ``DATA_DIR``.

        Args:
            absolute_path: Path inside ``DATA_DIR``.

        Returns:
            Relative path string, or an empty string when ``absolute_path``
            equals ``DATA_DIR``.

        """
        relative = absolute_path.relative_to(self.DATA_DIR.resolve())
        return str(relative) if str(relative) != "." else ""

    def get_instance_dir(self, path: str, /) -> Path:
        """Resolve an instance path and verify that its manifest exists.

        Args:
            path: Instance name or relative path.

        Returns:
            Absolute path to the instance directory.

        Raises:
            InstanceNotFoundError: If the directory or its manifest is missing.

        """
        target_dir = self._resolve_path(path)
        if not target_dir.joinpath(self.MANIFEST_FILE_NAME).exists():
            raise InstanceNotFoundError(path)
        return target_dir
