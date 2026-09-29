from __future__ import annotations


class InvalidManifestPathError(ValueError):
    """Raised when the requested manifest path is invalid."""

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


class InstanceAlreadyRunningError(RuntimeError):
    """Raised when the requested instance is already running."""

    def __init__(self, instance: str) -> None:
        super().__init__(f"Instance {instance!r} is already running")


class InstanceNotFoundError(ValueError):
    """Raised when the requested instance does not exist."""

    def __init__(self, instance: str) -> None:
        super().__init__(f"Instance {instance!r} does not exist")
