"""Manifest-backed game server base with CRUD template methods."""

from __future__ import annotations

import asyncio
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Protocol

from src.game.base import GameServer
from src.game.error import (
    InstanceNotFoundError,
    InvalidManifestPathError,
    ManifestAlreadyExistsError,
    ManifestNotFoundError,
)


class ManifestModel(Protocol):
    """Structural interface satisfied by every persisted manifest model."""

    path: str

    def to_dict(self) -> dict: ...


class ManifestGameServer[ManifestT: ManifestModel](GameServer, ABC):
    """Base class for game servers that persist per-instance manifests.

    In addition to the helpers provided by :class:`GameServer`, this class
    adds safe path resolution and relative-path conversion for manifest files
    stored inside each instance directory.

    Manifest CRUD is implemented as template methods on top of three hooks:
    ``_read_sync`` parses a manifest file into the game's persisted model,
    while ``_create_manifest_model`` and ``_update_manifest_model`` build the
    model from creation/update arguments. Subclasses supply the hooks; the
    template methods own directory creation, JSON serialization and path
    bookkeeping.
    """

    MANIFEST_FILE_NAME: ClassVar[str] = "atlantis.json"
    """Filename used for the per-instance manifest."""

    async def display_manifests(self) -> list[ManifestT]:
        """Return every persisted manifest under ``DATA_DIR``.

        The directory walk is executed in a thread to avoid blocking the event
        loop on slow filesystem operations.

        Returns:
            Manifests sorted by their directory path.

        """

        def _walk() -> list[ManifestT]:
            manifests: list[ManifestT] = []
            for manifest_path in sorted(self.DATA_DIR.rglob(self.MANIFEST_FILE_NAME)):
                relative_path = self._relative_path(manifest_path.parent)
                manifests.append(self._read_sync(manifest_path, relative_path))
            return manifests

        return await asyncio.to_thread(_walk)

    async def create_manifest(self, **kwargs: object) -> ManifestT:
        """Create a new timestamped instance and persist its manifest.

        Args:
            **kwargs: Game-specific creation arguments forwarded to
                :meth:`_create_manifest_model`.

        Returns:
            The persisted manifest model.

        Raises:
            ManifestAlreadyExistsError: If the generated instance path already
                holds a manifest.

        """
        path = await self.create_instance()
        target_dir = self._resolve_path(path)
        manifest_path = target_dir.joinpath(self.MANIFEST_FILE_NAME)

        if manifest_path.exists():
            raise ManifestAlreadyExistsError(self._relative_path(target_dir))

        def _write() -> ManifestT:
            target_dir.mkdir(parents=True, exist_ok=True)
            manifest = self._create_manifest_model(target_dir, **kwargs)
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )
            return manifest

        return await asyncio.to_thread(_write)

    async def update_manifest(self, path: str, /, **kwargs: object) -> ManifestT:
        """Update the manifest at ``path`` with the provided arguments.

        Args:
            path: Relative instance path to the manifest.
            **kwargs: Game-specific update arguments forwarded to
                :meth:`_update_manifest_model`; unspecified fields are kept
                from the existing manifest.

        Returns:
            The updated manifest model.

        Raises:
            ManifestNotFoundError: If the manifest does not exist at ``path``.

        """
        target_dir = self._resolve_path(path)
        manifest_path = target_dir.joinpath(self.MANIFEST_FILE_NAME)

        if not manifest_path.exists():
            raise ManifestNotFoundError(self._relative_path(target_dir))

        existing = await asyncio.to_thread(
            self._read_sync,
            manifest_path,
            self._relative_path(target_dir),
        )

        def _write() -> ManifestT:
            manifest = self._update_manifest_model(target_dir, existing, **kwargs)
            manifest_path.write_text(
                json.dumps(manifest.to_dict(), indent=2) + "\n",
                encoding="utf-8",
            )
            return manifest

        return await asyncio.to_thread(_write)

    @abstractmethod
    def _read_sync(self, manifest_path: Path, relative_path: str, /) -> ManifestT:
        """Parse the manifest file at ``manifest_path`` into a persisted model.

        Args:
            manifest_path: Absolute path to the manifest file.
            relative_path: Instance path relative to ``DATA_DIR``.

        """

    @abstractmethod
    def _create_manifest_model(self, target_dir: Path, /, **kwargs: object) -> ManifestT:
        """Build the persisted model for a new manifest at ``target_dir``.

        Args:
            target_dir: Absolute instance directory for the new manifest.
            **kwargs: Game-specific creation arguments.

        """

    @abstractmethod
    def _update_manifest_model(
        self,
        target_dir: Path,
        existing: ManifestT,
        /,
        **kwargs: object,
    ) -> ManifestT:
        """Build the updated model by merging ``kwargs`` over ``existing``.

        Args:
            target_dir: Absolute instance directory of the manifest.
            existing: Currently persisted manifest model.
            **kwargs: Game-specific update arguments.

        """

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
