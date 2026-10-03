from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import aiodocker
from aiodocker.containers import DockerContainer
from aiodocker.exceptions import DockerError
from aiodocker.types import JSONValue

from src.app import App

_HTTP_NOT_FOUND = 404


class Docker:
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
        host_config: dict[str, JSONValue] = {}
        binds: list[str] = []

        if volumes:
            binds.extend(f"{host_path}:{container_path}" for host_path, container_path in volumes.items())

        if read_only_volumes:
            binds.extend(f"{host_path}:{container_path}:ro" for host_path, container_path in read_only_volumes.items())

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

        return await self._docker.containers.run(config=config, name=self.get_container_name(name))

    async def get_container(self, name: str, /) -> DockerContainer | None:
        try:
            return await self._docker.containers.get(self.get_container_name(name))
        except DockerError as exc:
            if exc.status == _HTTP_NOT_FOUND:
                return None
            raise

    async def stop(self, name: str, /) -> None:
        container = await self.get_container(name)
        if container is None:
            return

        await container.stop()
        await container.delete(force=True)

    async def is_running(self, name: str, /) -> bool:
        try:
            container = await self.get_container(name)
            if container is None:
                return False
        except DockerError as exc:
            if exc.status == _HTTP_NOT_FOUND:
                return False
            raise

        info = await container.show()
        return info.get("State", {}).get("Running", False) is True

    async def get_host_port(self, name: str | DockerContainer, /, *, protocol: str = "udp") -> int | None:
        try:
            container = await self.get_container(name) if isinstance(name, str) else name
            if container is None:
                return None
        except DockerError as exc:
            if exc.status == _HTTP_NOT_FOUND:
                return None
            raise

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
            containers = await self._docker.containers.list(
                all=True,
                # filters={"label": [f"atlantis.game={game}"]},
            )

            used_ports: set[int] = set()
            for container in containers:
                info = await container.show()
                ports = info.get("NetworkSettings", {}).get("Ports", {})
                for port_proto, bindings in ports.items():
                    if not port_proto.endswith(f"/{protocol}"):
                        continue

                    for binding in bindings or []:
                        host_port = binding.get("HostPort")
                        if host_port is not None:
                            used_ports.add(int(host_port))

            for offset in range(max_attempts):
                candidate = base + offset
                if candidate not in used_ports:
                    yield candidate
                    return

            msg = f"No free port found after {max_attempts} attempts starting from {base}"
            raise RuntimeError(msg)
