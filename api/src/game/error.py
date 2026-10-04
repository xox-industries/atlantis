from __future__ import annotations


class InstanceNotFoundError(ValueError):
    """Raised when the requested game instance does not exist."""

    def __init__(self, instance: str) -> None:
        super().__init__(f"Instance {instance!r} does not exist")


class InstanceAlreadyRunningError(RuntimeError):
    """Raised when the requested game instance is already running."""

    def __init__(self, instance: str) -> None:
        super().__init__(f"Instance {instance!r} is already running")


class InstanceNotRunningError(RuntimeError):
    """Raised when the requested game instance is not running."""

    def __init__(self, instance: str) -> None:
        super().__init__(f"Instance {instance!r} is not running")


class InvalidManifestPathError(ValueError):
    """Raised when a manifest path is outside the game data directory or otherwise invalid."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Invalid manifest path {path!r}")


class ManifestNotFoundError(ValueError):
    """Raised when the requested manifest does not exist."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Manifest {path!r} does not exist")


class ManifestAlreadyExistsError(ValueError):
    """Raised when a manifest already exists at the requested path."""

    def __init__(self, path: str) -> None:
        super().__init__(f"Manifest already exists at {path!r}")
