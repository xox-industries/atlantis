from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Literal

from aiodocker.containers import DockerContainer
from aiodocker.stream import Message, Stream

from src.app import App
from src.docker import Docker
from src.minecraft_java_edition import MinecraftJavaEdition
from src.palworld import Palworld
from src.steam import Steam
from src.terraria import Terraria
from src.tmodloader import TModLoader
from src.valheim import Valheim


def make_terraria(app: App, data_dir: Path) -> Terraria:
    class TestTerraria(Terraria):
        DATA_DIR = data_dir

    return TestTerraria(app)


def make_tmodloader(app: App, data_dir: Path) -> TModLoader:
    class TestTModLoader(TModLoader):
        DATA_DIR = data_dir

    return TestTModLoader(app)


def make_minecraft(app: App, data_dir: Path) -> MinecraftJavaEdition:
    class TestMinecraft(MinecraftJavaEdition):
        DATA_DIR = data_dir

    return TestMinecraft(app)


def make_palworld(app: App, data_dir: Path) -> Palworld:
    class TestPalworld(Palworld):
        DATA_DIR = data_dir

    return TestPalworld(app)


def make_valheim(app: App, data_dir: Path) -> Valheim:
    class TestValheim(Valheim):
        DATA_DIR = data_dir

    return TestValheim(app)


async def _fake_steamcmd_output() -> AsyncGenerator[str]:
    yield "ok"


class RecordingSteam(Steam):
    """Steam fake that records ``validate_app`` calls instead of running SteamCMD."""

    def __init__(self) -> None:
        self.validate_calls: list[dict[str, Any]] = []

    async def validate_app(
        self,
        *,
        app_id: str,
        anonymous: bool = False,
        platform: Literal["windows", "linux"] = "linux",
        beta_branch: str | None = None,
    ) -> AsyncGenerator[str]:
        self.validate_calls.append(
            {
                "app_id": app_id,
                "anonymous": anonymous,
                "platform": platform,
                "beta_branch": beta_branch,
            },
        )
        return _fake_steamcmd_output()


class FakeStream(Stream):
    """Fake attach stream capturing written commands and replaying output."""

    def __init__(self, output: list[bytes] | None = None) -> None:
        self._resp = None
        self.writes: list[bytes] = []
        self.closed = False
        self.output = output or []

    async def write_in(self, data: bytes) -> None:
        self.writes.append(data)

    async def read_out(self) -> Message | None:
        if not self.output:
            return None
        return Message(stream=1, data=self.output.pop(0))

    async def close(self) -> None:
        self.closed = True


class FakeContainer(DockerContainer):
    """DockerContainer fake tracking attach/wait/delete interactions."""

    def __init__(self, name: str, /) -> None:
        self.name = name
        self.running = True
        self.deleted = False
        self.attach_count = 0
        self.stream = FakeStream()

    async def show(self, **kwargs: object) -> dict[str, Any]:
        return {"State": {"Running": self.running}}

    def attach(self, **kwargs: object) -> FakeStream:
        self.attach_count += 1
        return self.stream

    async def wait(self, **kwargs: object) -> dict[str, Any]:
        self.running = False
        return {}

    async def delete(self, **kwargs: object) -> None:
        self.deleted = True


class FakeDocker(Docker):
    """Docker fake recording container interactions without a daemon."""

    def __init__(self) -> None:
        self.containers: dict[str, FakeContainer] = {}
        self.stopped: list[str] = []
        self.run_calls: list[dict[str, Any]] = []

    async def get_container(self, name: str, /) -> DockerContainer | None:
        return self.containers.get(name)

    async def stop(self, name: str, /) -> None:
        self.stopped.append(name)
        container = self.containers.get(name)
        if container is not None:
            container.running = False

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
        self.run_calls.append(
            {
                "name": name,
                "image": image,
                "command": command,
                "volumes": volumes,
                "read_only_volumes": read_only_volumes,
                "ports": ports,
                "env": env,
                "labels": labels,
                "working_dir": working_dir,
            },
        )
        container = FakeContainer(name)
        self.containers[name] = container
        return container

    @asynccontextmanager
    async def find_free_port(
        self,
        *,
        base: int,
        game: str,
        protocol: str = "udp",
        max_attempts: int = 100,
    ) -> AsyncGenerator[int]:
        yield base
