from __future__ import annotations

import os

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
        }

        if labels:
            config["Labels"] = labels

        if working_dir:
            config["WorkingDir"] = working_dir

        if exposed_ports:
            config["ExposedPorts"] = exposed_ports

        return await self._docker.containers.run(config=config, name=f"atlantis-{name}")

    async def stop(self, name: str, /) -> None:
        try:
            container = await self._docker.containers.get(name)
        except DockerError as exc:
            if exc.status == _HTTP_NOT_FOUND:
                return
            raise

        await container.stop()
        await container.delete(force=True)

    async def is_running(self, name: str, /) -> bool:
        try:
            container = await self._docker.containers.get(name)
        except DockerError as exc:
            if exc.status == _HTTP_NOT_FOUND:
                return False
            raise

        info = await container.show()
        return info.get("State", {}).get("Running", False) is True

    async def get_host_port(self, container: str | DockerContainer, /, *, protocol: str = "udp") -> int | None:
        try:
            container = await self._docker.containers.get(container) if isinstance(container, str) else container
        except DockerError as exc:
            if exc.status == _HTTP_NOT_FOUND:
                return None
            raise

        info = await container.show()
        port_bindings = info.get("HostConfig", {}).get("PortBindings", {})
        for key, bindings in port_bindings.items():
            if key.endswith(f"/{protocol}") and bindings:
                host_port = bindings[0].get("HostPort")
                if host_port is not None:
                    return int(host_port)

        return None

    async def find_free_port(
        self,
        *,
        base: int,
        game: str,
        protocol: str = "udp",
        max_attempts: int = 100,
    ) -> int:
        containers = await self._docker.containers.list(
            all=True,
            filters={"label": [f"atlantis.game={game}"]},
        )

        used_ports: set[int] = set()
        for container in containers:
            info = await container.show()
            ports = info.get("Ports", [])
            for port in ports:
                if port.get("Type") == protocol:
                    public_port = port.get("PublicPort")
                    if isinstance(public_port, int):
                        used_ports.add(public_port)

        for offset in range(max_attempts):
            candidate = base + offset
            if candidate not in used_ports:
                return candidate

        msg = f"No free port found after {max_attempts} attempts starting from {base}"
        raise RuntimeError(msg)
