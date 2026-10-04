from __future__ import annotations

from pathlib import Path

from src.app import App
from test.game._helpers import (
    FakeContainer,
    FakeDocker,
    FakeStream,
    make_minecraft,
    make_palworld,
    make_terraria,
    make_tmodloader,
    make_valheim,
)


async def test_interactive_stop_writes_command_and_streams_output(
    app: App,
    tmp_path: Path,
) -> None:
    docker = FakeDocker()
    app.docker = docker
    game = make_terraria(app, tmp_path / "terraria")
    container = FakeContainer("atlantis-terraria-ses_0001")
    container.stream = FakeStream(output=[b"Server shutting down"])
    docker.containers["terraria-ses_0001"] = container

    lines = [line async for line in game.stop("ses_0001")]

    assert lines == [
        "Attaching to container and sending stop command",
        "Server shutting down",
        "Waiting for container to stop",
        "Container stopped",
    ]
    assert container.stream.writes == [b"exit\n"]
    assert container.stream.closed is True
    assert container.deleted is True
    assert container.attach_count == 1


async def test_minecraft_stop_sends_stop_command(app: App, tmp_path: Path) -> None:
    docker = FakeDocker()
    app.docker = docker
    game = make_minecraft(app, tmp_path / "minecraft")
    container = FakeContainer("atlantis-minecraft-java-edition-ses_0001")
    docker.containers["minecraft-java-edition-ses_0001"] = container

    lines = [line async for line in game.stop("ses_0001")]

    assert "Attaching to container and sending stop command" in lines
    assert "Container stopped" in lines
    assert container.stream.writes == [b"stop\n"]
    assert container.deleted is True


async def test_tmodloader_stop_sends_exit_command(app: App, tmp_path: Path) -> None:
    docker = FakeDocker()
    app.docker = docker
    game = make_tmodloader(app, tmp_path / "tmodloader")
    container = FakeContainer("atlantis-tmodloader-ses_0001")
    docker.containers["tmodloader-ses_0001"] = container

    lines = [line async for line in game.stop("ses_0001")]

    assert "Container stopped" in lines
    assert container.stream.writes == [b"exit\n"]
    assert container.deleted is True


async def test_interactive_stop_not_running_deletes_container(
    app: App,
    tmp_path: Path,
) -> None:
    docker = FakeDocker()
    app.docker = docker
    game = make_terraria(app, tmp_path / "terraria")
    container = FakeContainer("atlantis-terraria-ses_0001")
    container.running = False
    docker.containers["terraria-ses_0001"] = container

    lines = [line async for line in game.stop("ses_0001")]

    assert lines == ["Instance is not running"]
    assert container.deleted is True
    assert container.attach_count == 0


async def test_interactive_stop_missing_container_yields_not_found(
    app: App,
    tmp_path: Path,
) -> None:
    docker = FakeDocker()
    app.docker = docker
    game = make_terraria(app, tmp_path / "terraria")

    lines = [line async for line in game.stop("unknown")]

    assert lines == ["Container not found"]


async def test_simple_stop_delegates_to_docker(app: App, tmp_path: Path) -> None:
    docker = FakeDocker()
    app.docker = docker
    palworld = make_palworld(app, tmp_path / "palworld")
    valheim = make_valheim(app, tmp_path / "valheim")

    await palworld.stop("ses_0001")
    await valheim.stop("ses_0002")

    assert docker.stopped == ["palworld-ses_0001", "valheim-ses_0002"]
