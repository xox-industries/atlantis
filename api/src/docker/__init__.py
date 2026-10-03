from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import overload

import aiodocker
from aiodocker.containers import DockerContainer
from aiodocker.exceptions import DockerError
from aiodocker.types import JSONValue
from starlette.status import HTTP_404_NOT_FOUND

from src.app import App


class Docker:
    """Thin async wrapper around `aiodocker` for managing sibling game containers.

    All Atlantis-owned containers are prefixed with ``atlantis-`` so they can be
    distinguished from unrelated Docker workloads on the host. The wrapper also
    owns a per-instance port lock so concurrent ``find_free_port`` callers do not
    race on the same host port.
    """

    def __init__(self, app: App, /) -> None:
        self._app = app
        self._docker = aiodocker.Docker()
        self._port_lock = asyncio.Lock()

    async def run(
        self,
        *,
        name: str,
        image: str,
        command: list[str],
        volumes: dict[str, str] | None = None,
        read_only_volumes: dict[str, str] | None = None,
        ports: dict[str, tuple[str, int]] | None = None,
        env: dict[str, str] | None = None,
        labels: dict[str, str] | None = None,
        working_dir: str | None = None,
    ) -> DockerContainer:
        """Create and start a sibling container with Atlantis defaults.

        Every container automatically receives ``UID`` and ``GID`` environment
        variables from the API process so the in-container entrypoint can map
        itself to the host user.
        """
        config = self._build_container_config(
            image=image,
            command=command,
            volumes=volumes,
            read_only_volumes=read_only_volumes,
            ports=ports,
            env=env,
            labels=labels,
            working_dir=working_dir,
        )
        return await self._docker.containers.run(config=config, name=self.get_container_name(name))

    def _build_container_config(
        self,
        *,
        image: str,
        command: list[str],
        volumes: dict[str, str] | None,
        read_only_volumes: dict[str, str] | None,
        ports: dict[str, tuple[str, int]] | None,
        env: dict[str, str] | None,
        labels: dict[str, str] | None,
        working_dir: str | None,
    ) -> dict[str, JSONValue]:
        """Build a Docker container create payload from high-level arguments."""
        host_config: dict[str, JSONValue] = {}
        binds = self._build_binds(volumes, read_only_volumes)
        if binds:
            host_config["Binds"] = binds

        exposed_ports: dict[str, dict[str, str]] = {}
        if ports:
            port_bindings: dict[str, list[dict[str, str]]] = {}
            for container_port_proto, (host_ip, host_port) in ports.items():
                port_bindings[container_port_proto] = [
                    {"HostIp": host_ip, "HostPort": str(host_port)},
                ]
                exposed_ports[container_port_proto] = {}
            host_config["PortBindings"] = port_bindings

        container_env: dict[str, str] = {
            "UID": os.environ["UID"],
            "GID": os.environ["GID"],
        }
        if env:
            container_env.update(env)

        config: dict[str, JSONValue] = {
            "Image": image,
            "Cmd": command,
            "HostConfig": host_config,
            "Env": [f"{k}={v}" for k, v in container_env.items()],
            "OpenStdin": True,
            "Tty": True,
        }

        if labels:
            config["Labels"] = labels

        if working_dir:
            config["WorkingDir"] = working_dir

        if exposed_ports:
            config["ExposedPorts"] = exposed_ports

        return config

    @staticmethod
    def _build_binds(
        volumes: dict[str, str] | None,
        read_only_volumes: dict[str, str] | None,
    ) -> list[str]:
        """Return Docker ``Binds`` entries for writable and read-only mounts."""
        binds: list[str] = []
        if volumes:
            binds.extend(f"{host_path}:{container_path}" for host_path, container_path in volumes.items())
        if read_only_volumes:
            binds.extend(f"{host_path}:{container_path}:ro" for host_path, container_path in read_only_volumes.items())
        return binds

    async def get_container(self, name: str, /) -> DockerContainer | None:
        """Fetch a container by logical Atlantis name, returning ``None`` if absent."""
        try:
            return await self._docker.containers.get(self.get_container_name(name))
        except DockerError as exc:
            if exc.status == HTTP_404_NOT_FOUND:
                return None
            raise

    async def stop(self, name: str, /) -> None:
        """Stop and remove the container if it exists; no-op otherwise."""
        container = await self.get_container(name)
        if container is None:
            return

        await container.stop()
        await container.delete(force=True)

    async def is_running(self, name: str, /) -> bool:
        """Return whether the named container exists and is in the running state."""
        container = await self.get_container(name)
        if container is None:
            return False

        info = await container.show()
        return bool(info.get("State", {}).get("Running"))

    @overload
    async def get_host_port(self, name: str, /, *, protocol: str = "udp") -> int | None: ...

    @overload
    async def get_host_port(self, container: DockerContainer, /, *, protocol: str = "udp") -> int | None: ...

    async def get_host_port(
        self,
        name_or_container: str | DockerContainer,
        /,
        *,
        protocol: str = "udp",
    ) -> int | None:
        """Return the host-bound port for ``protocol`` on the given container.

        The port is first looked up in the live network settings, then falls back
        to the configured port bindings. Returns ``None`` when the container is
        missing or has no binding for the requested protocol.
        """
        container = (
            await self.get_container(name_or_container) if isinstance(name_or_container, str) else name_or_container
        )
        if container is None:
            return None

        info = await container.show()
        network_port = self._extract_host_port(
            info.get("NetworkSettings", {}).get("Ports", {}),
            protocol,
        )
        if network_port is not None:
            return network_port

        return self._extract_host_port(
            info.get("HostConfig", {}).get("PortBindings", {}),
            protocol,
        )

    def _extract_host_port(self, port_map: dict[str, JSONValue], protocol: str, /) -> int | None:
        """Scan a Docker port mapping for the first host port matching ``protocol``."""
        for container_port_proto, bindings in port_map.items():
            if not isinstance(container_port_proto, str) or not container_port_proto.endswith(f"/{protocol}"):
                continue
            if not isinstance(bindings, list):
                continue
            for binding in bindings:
                if not isinstance(binding, dict):
                    continue
                host_port = binding.get("HostPort")
                if isinstance(host_port, str):
                    return int(host_port)
        return None

    def get_container_name(self, name: str, /) -> str:
        """Return the prefixed Docker container name for a logical Atlantis name."""
        return f"atlantis-{name}"

    @asynccontextmanager
    async def find_free_port(
        self,
        *,
        base: int,
        game: str,
        protocol: str = "udp",
        max_attempts: int = 100,
    ) -> AsyncGenerator[int]:
        """Yield a free host port while holding the allocation lock.

        The lock is held for the duration of the ``async with`` block so that
        the port cannot be claimed by another caller before the container is
        created.
        """
        async with self._port_lock:
            containers = await self._docker.containers.list(all=True)
            used_ports = await self._used_ports_for_protocol(containers, protocol)

            for offset in range(max_attempts):
                candidate = base + offset
                if candidate not in used_ports:
                    yield candidate
                    return

            msg = f"No free port found after {max_attempts} attempts starting from {base}"
            raise RuntimeError(msg)

    async def _used_ports_for_protocol(
        self,
        containers: list[DockerContainer],
        protocol: str,
        /,
    ) -> set[int]:
        """Collect host ports already bound for ``protocol`` across ``containers``."""
        used_ports: set[int] = set()
        for container in containers:
            info = await container.show()
            ports = info.get("NetworkSettings", {}).get("Ports", {})
            for port_proto, bindings in ports.items():
                if not isinstance(port_proto, str) or not port_proto.endswith(f"/{protocol}"):
                    continue
                for binding in bindings or []:
                    host_port = binding.get("HostPort")
                    if host_port is not None:
                        used_ports.add(int(host_port))
        return used_ports
