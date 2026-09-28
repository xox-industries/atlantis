from __future__ import annotations

import re
from typing import Any

import httpx
from bs4 import BeautifulSoup


class VersionValidationError(ValueError):
    """Raised when a version cannot be validated or retrieved."""


class UnsupportedModloaderError(VersionValidationError):
    """Raised when an unsupported modloader type is requested."""

    def __init__(self, modloader_type: str) -> None:
        super().__init__(f"Unsupported modloader type: {modloader_type}")


class VersionNotFoundError(VersionValidationError):
    """Raised when a requested version cannot be found."""

    def __init__(self, *, context: str, version: str = "") -> None:
        if version:
            super().__init__(f"{context} not found for {version}")
        else:
            super().__init__(f"{context} not found")


class ExternalServiceError(VersionValidationError):
    """Raised when an external version service request fails."""

    def __init__(self, service: str) -> None:
        super().__init__(f"Failed to contact {service}")


_MINECRAFT_VERSION_MANIFEST_URL = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
_FABRIC_LOADER_VERSIONS_URL = "https://meta.fabricmc.net/v2/versions/loader"
_FORGE_INDEX_URL_TEMPLATE = "https://files.minecraftforge.net/net/minecraftforge/forge/index_{minecraft_version}.html"
_FORGE_INSTALLER_URL_TEMPLATE = (
    "https://maven.minecraftforge.net/net/minecraftforge/forge/"
    "{minecraft_version}-{modloader_version}/"
    "forge-{minecraft_version}-{modloader_version}-installer.jar"
)
_NEOFORGE_VERSIONS_URL = "https://maven.neoforged.net/api/maven/versions/releases/net/neoforged/neoforge"
_NEOFORGE_INSTALLER_URL_TEMPLATE = (
    "https://maven.neoforged.net/releases/net/neoforged/neoforge/"
    "{modloader_version}/neoforge-{modloader_version}-installer.jar"
)

_MINECRAFT_VERSION_PARTS = 2
_OK_STATUS = 200

_LATEST_MINECRAFT_CONTEXT = "Latest Minecraft version"
_FORGE_VERSION_CONTEXT = "Forge version"
_NEOFORGE_VERSION_CONTEXT = "NeoForge version"
_FABRIC_VERSION_CONTEXT = "Fabric loader version"
_MINECRAFT_VERSION_CONTEXT = "Minecraft version"


async def get_latest_minecraft_version() -> str:
    """Return the latest Minecraft release version from Mojang's manifest."""
    data = await _fetch_json(_MINECRAFT_VERSION_MANIFEST_URL, service="Mojang")
    latest = data.get("latest", {}).get("release")
    if not isinstance(latest, str):
        raise VersionNotFoundError(context=_LATEST_MINECRAFT_CONTEXT)
    return latest


async def validate_version(
    version_type: str,
    minecraft_version: str,
    modloader_version: str | None = None,
) -> bool:
    """Validate that a Minecraft or modloader version exists."""
    if version_type == "minecraft":
        return await _validate_minecraft_version(minecraft_version)

    if modloader_version is None:
        return False

    if version_type == "forge":
        return await _validate_forge_version(minecraft_version, modloader_version)
    if version_type == "neoforge":
        return await _validate_neoforge_version(modloader_version)
    if version_type == "fabric":
        return await _validate_fabric_version(modloader_version)

    raise UnsupportedModloaderError(version_type)


async def get_latest_modloader_version(
    modloader_type: str,
    minecraft_version: str,
) -> str:
    """Return the latest modloader version for the given Minecraft version."""
    if modloader_type == "forge":
        return await _get_latest_forge_version(minecraft_version)
    if modloader_type == "neoforge":
        return await _get_latest_neoforge_version(minecraft_version)
    if modloader_type == "fabric":
        return await _get_latest_fabric_version()

    raise UnsupportedModloaderError(modloader_type)


async def _validate_minecraft_version(minecraft_version: str) -> bool:
    data = await _fetch_json(_MINECRAFT_VERSION_MANIFEST_URL, service="Mojang")
    versions = data.get("versions", [])
    return any(version.get("id") == minecraft_version for version in versions)


async def _validate_forge_version(
    minecraft_version: str,
    modloader_version: str,
) -> bool:
    url = _FORGE_INSTALLER_URL_TEMPLATE.format(
        minecraft_version=minecraft_version,
        modloader_version=modloader_version,
    )
    return await _head_exists(url)


async def _validate_neoforge_version(modloader_version: str) -> bool:
    url = _NEOFORGE_INSTALLER_URL_TEMPLATE.format(modloader_version=modloader_version)
    return await _head_exists(url)


async def _validate_fabric_version(modloader_version: str) -> bool:
    versions = await _fetch_json_list(_FABRIC_LOADER_VERSIONS_URL, service="Fabric")
    return any(version.get("version") == modloader_version for version in versions)


async def _get_latest_forge_version(minecraft_version: str) -> str:
    url = _FORGE_INDEX_URL_TEMPLATE.format(minecraft_version=minecraft_version)
    html = await _fetch_text(url, service="Forge")
    soup = BeautifulSoup(html, "html.parser")

    promo = soup.select_one("i.fa.promo-latest")
    if promo is None:
        raise VersionNotFoundError(
            context=_FORGE_VERSION_CONTEXT,
            version=minecraft_version,
        )

    parent = promo.find_parent()
    if parent is None:
        raise VersionNotFoundError(
            context=_FORGE_VERSION_CONTEXT,
            version=minecraft_version,
        )

    text = parent.select_one("br + small")
    if text is None:
        raise VersionNotFoundError(
            context=_FORGE_VERSION_CONTEXT,
            version=minecraft_version,
        )

    version_text = text.get_text(strip=True).replace(" ", "")
    parts = version_text.split("-")
    if len(parts) < _MINECRAFT_VERSION_PARTS:
        raise VersionNotFoundError(
            context=_FORGE_VERSION_CONTEXT,
            version=minecraft_version,
        )

    return parts[1]


async def _get_latest_neoforge_version(minecraft_version: str) -> str:
    parts = minecraft_version.split(".")
    if len(parts) < _MINECRAFT_VERSION_PARTS:
        raise VersionNotFoundError(
            context=_MINECRAFT_VERSION_CONTEXT,
            version=minecraft_version,
        )

    minor = parts[1]
    patch = parts[2] if len(parts) > _MINECRAFT_VERSION_PARTS else "0"
    prefix = f"{minor}.{patch}."

    data = await _fetch_json(_NEOFORGE_VERSIONS_URL, service="NeoForge")
    versions = data.get("versions", [])
    matching = [version for version in versions if version.startswith(prefix)]
    if not matching:
        raise VersionNotFoundError(
            context=_NEOFORGE_VERSION_CONTEXT,
            version=minecraft_version,
        )

    return matching[-1]


async def _get_latest_fabric_version() -> str:
    versions = await _fetch_json_list(_FABRIC_LOADER_VERSIONS_URL, service="Fabric")
    stable_versions = [version for version in versions if version.get("stable")]
    if not stable_versions:
        raise VersionNotFoundError(context=_FABRIC_VERSION_CONTEXT)

    latest = max(stable_versions, key=_version_key)
    return latest.get("version", "")


async def _fetch_json(url: str, *, service: str) -> dict[str, Any]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=30)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(service) from exc
        response.raise_for_status()
        return response.json()


async def _fetch_json_list(url: str, *, service: str) -> list[dict[str, Any]]:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=30)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(service) from exc
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise VersionNotFoundError(context=_FABRIC_VERSION_CONTEXT)
        return data


async def _fetch_text(url: str, *, service: str) -> str:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.get(url, timeout=30)
        except httpx.HTTPError as exc:
            raise ExternalServiceError(service) from exc
        response.raise_for_status()
        return response.text


async def _head_exists(url: str) -> bool:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        try:
            response = await client.head(url, timeout=30)
        except httpx.HTTPError:
            return False
    return response.status_code == _OK_STATUS


def _version_key(version: dict[str, Any]) -> tuple[int, ...]:
    version_str = version.get("version", "")
    return tuple(int(part) for part in re.split(r"\D+", version_str) if part.isdigit())
