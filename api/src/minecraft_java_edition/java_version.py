# ruff: noqa: PLR0911, PLR2004

from __future__ import annotations

from packaging.version import Version


class UnknownMinecraftVersionError(ValueError):
    """Raised when a Minecraft version cannot be mapped to a Java version."""

    def __init__(self, minecraft_version: str) -> None:
        super().__init__(f"Cannot determine Java version for Minecraft {minecraft_version!r}")


def get_java_version(minecraft_version: str, /) -> int:
    """Return the JDK major version required for a given Minecraft release.

    Mapping based on official Minecraft system requirements:
    - 26.1+ (snapshots and newer year-based releases): Java 25
    - 1.20.5, 1.20.6, 1.21+: Java 21
    - 1.18 through 1.20.4: Java 17
    - 1.17 through 1.17.1: Java 17 (Java 16 is the documented minimum, but OpenJDK 16
      is not packaged by Ubuntu LTS; OpenJDK 17 is backward-compatible)
    - 1.12 through 1.16.5: Java 8
    - 1.6.1 through 1.11.2: Java 8 (Java 6+ acceptable, but Java 8 is the practical floor)
    - Older versions: Java 8 (Java 5+ acceptable)
    """
    version = _parse(minecraft_version)

    # Year-based versioning starting with 26.x
    if version.major >= 26:
        return 25

    # Pre-1.6: Java 8 is the lowest version widely available in modern distros.
    if version.major == 0 or (version.major == 1 and version.minor < 6):
        return 8

    # 1.6.1 through 1.11.2: Java 6 or newer; use Java 8 for availability.
    if version.major == 1 and version.minor <= 11:
        return 8

    # 1.12 through 1.16.5: Java 8
    if version.major == 1 and version.minor <= 16:
        return 8

    if version.major == 1 and version.minor == 17:
        return 17

    if version.major == 1 and version.minor == 20 and version.micro >= 5:
        return 21

    if version.major == 1 and version.minor == 20 and version.micro <= 4:
        return 17
    if version.major == 1 and version.minor in {18, 19}:
        return 17

    if version.major == 1 and version.minor >= 21:
        return 21

    msg = f"Cannot determine Java version for Minecraft {minecraft_version!r}"
    raise UnknownMinecraftVersionError(msg)


def _parse(version: str, /) -> Version:
    """Parse a Minecraft version string, normalizing snapshots."""
    cleaned = version.lower().lstrip("v")

    # Normalize snapshots like 25w50a or 26w02a to a year-based version.
    if len(cleaned) >= 5 and cleaned[2] == "w" and cleaned[-1].isalpha():
        year = int(cleaned[:2])
        return Version(f"{year + 2000}.0.0")

    # Strip trailing snapshot suffixes such as -pre1, -rc1, .1 (Forge style).
    base = cleaned.split("-")[0]
    parts = base.split(".")
    while len(parts) < 3:
        parts.append("0")

    return Version(".".join(parts[:3]))
