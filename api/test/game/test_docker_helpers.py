from __future__ import annotations

from pathlib import Path

import pytest

from src.app import App
from test.game._helpers import (
    FakeContainer,
    FakeDocker,
    make_palworld,
    make_terraria,
    make_tmodloader,
    make_valheim,
)


def test_terraria_command_volumes_ports_and_labels(app: App, tmp_path: Path) -> None:
    game = make_terraria(app, tmp_path / "terraria")

    command = " ".join(game._build_command("ses_0001"))
    assert "/home/app/Terraria/TerrariaServer.bin.x86_64" in command
    assert "-config /home/app/.local/share/Terraria/manifest.conf" in command

    target = tmp_path / "terraria" / "ses_0001"
    assert game._build_volumes(target) == {
        str(App.get_host_path(target)): "/home/app/.local/share/Terraria",
    }
    assert game._build_read_only_volumes() == {
        str(App.get_host_path(game.APP_DIR)): str(game.APP_DIR),
    }
    assert game._build_ports(9000) == {"7777/tcp": ("0.0.0.0", 9000)}
    assert game._build_labels("ses_0001") == {
        "atlantis.game": "terraria",
        "atlantis.instance": "ses_0001",
    }


def test_tmodloader_command_has_nosteam_flags(app: App, tmp_path: Path) -> None:
    game = make_tmodloader(app, tmp_path / "tmodloader")

    command = " ".join(game._build_command("ses_0001"))
    assert "/home/app/tModLoader/start-tModLoaderServer.sh" in command
    assert "-nosteam" in command
    assert "-tmlsavedirectory /home/app/.local/share/Terraria" in command
    assert "-steamworkshopfolder none" in command
    assert game._build_ports(9001) == {"7777/tcp": ("0.0.0.0", 9001)}
    assert game._build_labels("ses_0001") == {
        "atlantis.game": "tmodloader",
        "atlantis.instance": "ses_0001",
    }


def test_palworld_command_volumes_and_ports(app: App, tmp_path: Path) -> None:
    game = make_palworld(app, tmp_path / "palworld")
    target = tmp_path / "palworld" / "myinstance"
    target.mkdir(parents=True)

    command = " ".join(game._build_command("myinstance"))
    assert "PalServer.exe" in command
    assert "-port=8211" in command
    assert "wineprefix" in command
    assert "tar -C" in command
    assert "ln -s" not in command

    assert game._build_volumes(target) == {
        str(App.get_host_path(target / "Saved")): str(game.CONTAINER_APP_DIR.joinpath("Pal", "Saved")),
        str(App.get_host_path(target / "Mods")): str(game.CONTAINER_APP_DIR.joinpath("Mods")),
    }
    read_only_volumes = game._build_read_only_volumes()
    assert read_only_volumes == {
        str(App.get_host_path(game.APP_DIR)): str(game.APP_DIR),
        str(App.get_host_path(game._app.WINE_DIR)): str(game._app.WINE_DIR),
    }
    assert game._build_ports(9002) == {"8211/udp": ("0.0.0.0", 9002)}
    assert game._build_labels("myinstance") == {
        "atlantis.game": "palworld",
        "atlantis.instance": "myinstance",
    }


def test_valheim_command_volumes_and_ports(app: App, tmp_path: Path) -> None:
    game = make_valheim(app, tmp_path / "valheim")

    command = " ".join(game._build_command("myinstance"))
    assert "valheim_server.x86_64" in command
    assert "-name 'myinstance'" in command
    assert "-port 2456" in command
    assert "-crossplay" in command

    target = tmp_path / "valheim" / "myinstance"
    assert game._build_volumes(target) == {
        str(App.get_host_path(target)): "/home/app/.config/unity3d/IronGate/Valheim",
    }
    assert game._build_ports(9003) == {"2456/udp": ("0.0.0.0", 9003)}
    assert game._build_labels("myinstance") == {
        "atlantis.game": "valheim",
        "atlantis.instance": "myinstance",
    }


async def test_terraria_writes_server_config(app: App, tmp_path: Path) -> None:
    game = make_terraria(app, tmp_path / "terraria")
    created = await game.create_manifest(
        game_autocreate=1,
        game_seed="seed-1",
        game_difficulty=2,
        game_password="pw",
        game_motd="hi",
    )

    await game._ensure_instance_dirs(game.get_instance_dir(created.path))

    config = game.get_instance_dir(created.path).joinpath("manifest.conf").read_text()
    assert "world=/home/app/.local/share/Terraria/Worlds/world.wld" in config
    assert "autocreate=1" in config
    assert "seed=seed-1" in config
    assert "difficulty=2" in config
    assert "password=pw" in config
    assert "motd=hi" in config
    assert "port=7777" in config
    assert "npcstream=60" in config


async def test_palworld_creates_saved_and_mods_dirs(app: App, tmp_path: Path) -> None:
    game = make_palworld(app, tmp_path / "palworld")
    target = tmp_path / "palworld" / "ses_0001"
    target.mkdir(parents=True)

    await game._ensure_instance_dirs(target)

    assert target.joinpath("Saved").is_dir()
    assert target.joinpath("Mods").is_dir()


async def test_valheim_creates_worlds_dir(app: App, tmp_path: Path) -> None:
    game = make_valheim(app, tmp_path / "valheim")
    target = tmp_path / "valheim" / "ses_0001"
    target.mkdir(parents=True)

    await game._ensure_instance_dirs(target)

    assert target.joinpath("worlds_local").is_dir()


async def test_terraria_start_runs_container_without_docker(
    app: App,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DOCKER_IMAGE", "atlantis:test")
    docker = FakeDocker()
    app.docker = docker
    game = make_terraria(app, tmp_path / "terraria")
    created = await game.create_manifest(game_autocreate=1)
    name = game.get_instance_name(created.path)

    container = await game.start(created.path)

    assert isinstance(container, FakeContainer)
    assert container.name == name
    assert docker.stopped == [name]
    assert docker.run_calls == [
        {
            "name": name,
            "image": "atlantis:test",
            "command": game._build_command(created.path),
            "volumes": game._build_volumes(game.get_instance_dir(created.path)),
            "read_only_volumes": game._build_read_only_volumes(),
            "ports": game._build_ports(7777),
            "env": None,
            "labels": game._build_labels(created.path),
            "working_dir": None,
        },
    ]
