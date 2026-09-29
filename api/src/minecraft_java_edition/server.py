from __future__ import annotations

import asyncio
import re
from collections.abc import AsyncGenerator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import httpx

from src.minecraft_java_edition.model import PersistedMinecraftJavaEditionManifest

_FABRIC_INSTALLER_VERSION = "1.0.0"


@dataclass(frozen=True)
class _ServerContext:
    instance_dir: Path
    java: str
    ram: int
    jvm_arguments: list[str]


async def prepare_server(
    instance_dir: Path,
    manifest: PersistedMinecraftJavaEditionManifest,
) -> AsyncGenerator[str]:
    """Prepare the instance directory and yield setup logs."""
    java = _get_java_path(manifest.java_version)
    context = _ServerContext(
        instance_dir=instance_dir,
        java=java,
        ram=manifest.ram,
        jvm_arguments=manifest.jvm_arguments,
    )

    sign_eula(instance_dir)

    if manifest.modloader_type == "forge":
        async for line in setup_forge(
            context=context,
            minecraft_version=manifest.minecraft_version,
            modloader_version=manifest.modloader_version,
        ):
            yield line
    elif manifest.modloader_type == "neoforge":
        async for line in setup_neoforge(
            context=context,
            modloader_version=manifest.modloader_version,
        ):
            yield line
    elif manifest.modloader_type == "fabric":
        async for line in setup_fabric(
            context=context,
            minecraft_version=manifest.minecraft_version,
            modloader_version=manifest.modloader_version,
        ):
            yield line
    else:
        msg = f"Unsupported modloader type: {manifest.modloader_type}"
        raise RuntimeError(msg)


def build_server_command(
    instance_dir: Path,
    manifest: PersistedMinecraftJavaEditionManifest,
) -> list[str]:
    """Return the final server command for an already-prepared instance."""
    java = _get_java_path(manifest.java_version)
    jvm_arguments = [*manifest.jvm_arguments, *_read_user_jvm_args(instance_dir)]
    context = _ServerContext(
        instance_dir=instance_dir,
        java=java,
        ram=manifest.ram,
        jvm_arguments=jvm_arguments,
    )

    if manifest.modloader_type == "forge":
        return _build_forge_command(
            context=context,
            minecraft_version=manifest.minecraft_version,
            modloader_version=manifest.modloader_version,
        )
    if manifest.modloader_type == "neoforge":
        return _build_neoforge_command(
            context=context,
            modloader_version=manifest.modloader_version,
        )
    if manifest.modloader_type == "fabric":
        return _build_fabric_command(
            context=context,
            minecraft_version=manifest.minecraft_version,
            modloader_version=manifest.modloader_version,
        )

    msg = f"Unsupported modloader type: {manifest.modloader_type}"
    raise RuntimeError(msg)


def _get_java_path(java_version: int) -> str:
    java_path = Path(f"/usr/lib/jvm/java-{java_version}-openjdk-amd64/bin/java")
    if not java_path.exists():
        msg = f"Java {java_version} not found at {java_path}."
        raise RuntimeError(msg)
    return str(java_path)


def _read_user_jvm_args(instance_dir: Path) -> list[str]:
    """Read user-provided JVM args from the Forge/NeoForge args file."""
    args_path = instance_dir.joinpath("user_jvm_args.txt")
    if not args_path.exists():
        return []

    text = args_path.read_text(encoding="utf-8")
    args: list[str] = []
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        args.extend(stripped.split())
    return args


def sign_eula(instance_dir: Path) -> None:
    """Write eula.txt with eula=true."""
    eula_path = instance_dir.joinpath("eula.txt")
    lines = [
        "#By changing the setting below to TRUE you are indicating your agreement to our EULA (https://aka.ms/MinecraftEULA).",
        f"#{datetime.now(tz=UTC).isoformat()}",
        "eula=true",
    ]
    eula_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


async def _download(url: str, destination: Path) -> AsyncGenerator[str]:
    destination.parent.mkdir(parents=True, exist_ok=True)
    yield f"Downloading {destination.name}"
    async with httpx.AsyncClient(follow_redirects=True, timeout=300) as client:
        response = await client.get(url)
        response.raise_for_status()
        await asyncio.to_thread(destination.write_bytes, response.content)
    yield f"Downloaded {destination.name}"


async def _run_installer(java: str, installer: Path, cwd: Path) -> AsyncGenerator[str]:
    _stdout_unavailable_message = "Installer subprocess has no stdout"
    _installer_failed_message = "Installer failed"

    proc = await asyncio.create_subprocess_exec(
        java,
        "-jar",
        str(installer),
        "--installServer",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
        cwd=cwd,
    )

    if proc.stdout is None:
        raise RuntimeError(_stdout_unavailable_message)

    async for raw in proc.stdout:
        line = raw.decode(errors="replace").rstrip("\r\n")
        if line:
            yield line

    await proc.wait()

    if proc.returncode != 0:
        raise RuntimeError(_installer_failed_message)

    await asyncio.to_thread(installer.unlink, missing_ok=True)
    await asyncio.to_thread(installer.with_suffix(".jar.log").unlink, missing_ok=True)


async def setup_forge(
    *,
    context: _ServerContext,
    minecraft_version: str,
    modloader_version: str,
) -> AsyncGenerator[str]:
    library_path = context.instance_dir.joinpath(
        f"libraries/net/minecraftforge/forge/{minecraft_version}-{modloader_version}",
    )
    base_name = f"forge-{minecraft_version}-{modloader_version}"
    server_jar = library_path.joinpath(f"{base_name}-server.jar")
    universal_jar = library_path.joinpath(f"{base_name}-universal.jar")
    root_universal_jar = context.instance_dir.joinpath(f"{base_name}-universal.jar")
    legacy_jar = context.instance_dir.joinpath(f"{base_name}.jar")
    shim_jar = context.instance_dir.joinpath(f"{base_name}-shim.jar")
    installer_jar = context.instance_dir.joinpath(f"{base_name}-installer.jar")
    installer_url = (
        f"https://maven.minecraftforge.net/net/minecraftforge/forge/"
        f"{minecraft_version}-{modloader_version}/{base_name}-installer.jar"
    )

    installation_complete = (
        legacy_jar.exists() or root_universal_jar.exists() or (server_jar.exists() and universal_jar.exists())
    )

    if not installation_complete:
        if not installer_jar.exists():
            async for line in _download(installer_url, installer_jar):
                yield line
        yield "Installing Forge"
        async for line in _run_installer(context.java, installer_jar, context.instance_dir):
            yield line

    if shim_jar.exists():
        yield "Checking Java compatibility"
        proc = await asyncio.create_subprocess_exec(
            context.java,
            "-jar",
            str(shim_jar),
            "--onlyCheckJava",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            cwd=context.instance_dir,
        )
        if proc.stdout is not None:
            async for raw in proc.stdout:
                line = raw.decode(errors="replace").rstrip("\r\n")
                if line:
                    yield line
        await proc.wait()
        if proc.returncode != 0:
            _java_check_failed_message = "Java compatibility check failed"
            raise RuntimeError(_java_check_failed_message)


def _build_forge_command(
    *,
    context: _ServerContext,
    minecraft_version: str,
    modloader_version: str,
) -> list[str]:
    library_path = context.instance_dir.joinpath(
        f"libraries/net/minecraftforge/forge/{minecraft_version}-{modloader_version}",
    )
    base_name = f"forge-{minecraft_version}-{modloader_version}"
    legacy_jar = context.instance_dir.joinpath(f"{base_name}.jar")
    root_universal_jar = context.instance_dir.joinpath(f"{base_name}-universal.jar")
    library_universal_jar = library_path.joinpath(f"{base_name}-universal.jar")
    args_file = library_path.joinpath("unix_args.txt")

    base_command = _build_jvm_command(context)

    # Modern Forge (1.17+) ships an args file read by Java 9+ @argfile syntax.
    if args_file.exists():
        return [
            *base_command,
            f"@{args_file}",
            "nogui",
        ]

    # Older Forge is launched directly from a runnable jar (Java 8).
    # Forge 1.12.1 drops the runnable -universal.jar in the instance root.
    if legacy_jar.exists():
        return [*base_command, "-jar", str(legacy_jar), "nogui"]
    if root_universal_jar.exists():
        return [*base_command, "-jar", str(root_universal_jar), "nogui"]
    if library_universal_jar.exists():
        return [*base_command, "-jar", str(library_universal_jar), "nogui"]

    msg = (
        f"No Forge server launch target found for {minecraft_version}-{modloader_version}. "
        f"Expected one of: {args_file}, {legacy_jar}, {root_universal_jar}, {library_universal_jar}"
    )
    raise RuntimeError(msg)


async def setup_neoforge(
    *,
    context: _ServerContext,
    modloader_version: str,
) -> AsyncGenerator[str]:
    library_path = context.instance_dir.joinpath(f"libraries/net/neoforged/neoforge/{modloader_version}")
    base_name = f"neoforge-{modloader_version}"
    server_jar = library_path.joinpath(f"{base_name}-server.jar")
    universal_jar = library_path.joinpath(f"{base_name}-universal.jar")
    installer_jar = context.instance_dir.joinpath(f"{base_name}-installer.jar")
    installer_url = (
        f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{modloader_version}/{base_name}-installer.jar"
    )

    if not (server_jar.exists() and universal_jar.exists()):
        if not installer_jar.exists():
            async for line in _download(installer_url, installer_jar):
                yield line
        yield "Installing NeoForge"
        async for line in _run_installer(context.java, installer_jar, context.instance_dir):
            yield line


def _build_neoforge_command(
    *,
    context: _ServerContext,
    modloader_version: str,
) -> list[str]:
    library_path = context.instance_dir.joinpath(f"libraries/net/neoforged/neoforge/{modloader_version}")

    base_command = _build_jvm_command(context)
    return [
        *base_command,
        f"@{library_path.joinpath('unix_args.txt')}",
        "nogui",
    ]


async def setup_fabric(
    *,
    context: _ServerContext,
    minecraft_version: str,
    modloader_version: str,
) -> AsyncGenerator[str]:
    installer_jar = context.instance_dir.joinpath(
        f"fabric-server-mc.{minecraft_version}-loader.{modloader_version}-launcher.{_FABRIC_INSTALLER_VERSION}.jar",
    )
    installer_url = (
        f"https://meta.fabricmc.net/v2/versions/loader/"
        f"{minecraft_version}/{modloader_version}/{_FABRIC_INSTALLER_VERSION}/server/jar"
    )

    if not installer_jar.exists():
        async for line in _download(installer_url, installer_jar):
            yield line


def _build_fabric_command(
    *,
    context: _ServerContext,
    minecraft_version: str,
    modloader_version: str,
) -> list[str]:
    installer_jar = context.instance_dir.joinpath(
        f"fabric-server-mc.{minecraft_version}-loader.{modloader_version}-launcher.{_FABRIC_INSTALLER_VERSION}.jar",
    )
    base_command = _build_jvm_command(context)
    return [*base_command, "-jar", str(installer_jar), "nogui"]


def _build_jvm_command(context: _ServerContext) -> list[str]:
    xms = min(4096, context.ram)
    has_memory_flag = any(re.match(r"^-Xms|-Xmx", arg, re.IGNORECASE) for arg in context.jvm_arguments)
    command = [context.java, "-server"]
    if not has_memory_flag:
        command.extend([f"-Xms{xms}M", f"-Xmx{context.ram}M"])
    return [*command, *context.jvm_arguments]
