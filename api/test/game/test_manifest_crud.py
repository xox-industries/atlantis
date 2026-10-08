from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.app import App
from src.game.error import ManifestNotFoundError
from test.game._helpers import make_minecraft, make_terraria, make_tmodloader


async def test_create_display_and_persist_terraria_manifest(app: App, tmp_path: Path) -> None:
    game = make_terraria(app, tmp_path / "terraria")

    created = await game.create_manifest(
        steam_app_beta_branch="public-beta",
        game_autocreate=3,
        game_difficulty=2,
        game_motd="welcome",
        game_password="secret",
        game_seed="world-seed",
    )

    assert created.path.startswith("ses_")
    assert created.steam_app_beta_branch == "public-beta"
    assert created.game_autocreate == 3
    assert created.game_difficulty == 2
    assert created.game_motd == "welcome"
    assert created.game_password == "secret"
    assert created.game_seed == "world-seed"
    assert created.game_npcstream == 60
    assert created.game_secure is False
    assert created.game_upnp is True

    manifests = await game.display_manifests()
    assert [manifest.path for manifest in manifests] == [created.path]

    raw = json.loads(game.get_instance_dir(created.path).joinpath("trident.manifest.json").read_text())
    assert raw["terraria"]["autocreate"] == 3
    assert raw["terraria"]["steamAppBetaBranch"] == "public-beta"
    assert raw["manifestType"] == "terraria"
    assert raw["manifestVersion"] == 1


async def test_update_terraria_manifest_merges_over_existing(app: App, tmp_path: Path) -> None:
    game = make_terraria(app, tmp_path / "terraria")
    created = await game.create_manifest(
        steam_app_beta_branch="beta",
        game_autocreate=2,
        game_seed="seed1",
    )

    updated = await game.update_manifest(created.path, game_autocreate=4, game_seed="seed2")

    assert updated.game_autocreate == 4
    assert updated.game_seed == "seed2"
    assert updated.steam_app_beta_branch == "beta"
    assert updated.game_npcstream == 60
    assert updated.game_secure is False

    persisted = await game.display_manifests()
    assert persisted[0].game_autocreate == 4
    assert persisted[0].game_seed == "seed2"

    raw = json.loads(game.get_instance_dir(created.path).joinpath("trident.manifest.json").read_text())
    assert raw["terraria"]["autocreate"] == 4
    assert raw["terraria"]["seed"] == "seed2"
    assert raw["terraria"]["steamAppBetaBranch"] == "beta"


async def test_update_terraria_manifest_clears_optional_fields(app: App, tmp_path: Path) -> None:
    game = make_terraria(app, tmp_path / "terraria")
    created = await game.create_manifest(
        steam_app_beta_branch="beta",
        game_autocreate=2,
        game_motd="hello",
    )

    updated = await game.update_manifest(created.path, steam_app_beta_branch=None, game_motd=None)

    assert updated.steam_app_beta_branch is None
    assert updated.game_motd is None


async def test_update_missing_terraria_manifest_raises(app: App, tmp_path: Path) -> None:
    game = make_terraria(app, tmp_path / "terraria")

    with pytest.raises(ManifestNotFoundError):
        await game.update_manifest("missing-instance", game_autocreate=1)


async def test_display_manifests_sorts_by_path(app: App, tmp_path: Path) -> None:
    game = make_terraria(app, tmp_path / "terraria")
    created = await game.create_manifest(game_autocreate=1)

    second_dir = tmp_path / "terraria" / "ses_9999"
    second_dir.mkdir(parents=True)
    second_dir.joinpath("trident.manifest.json").write_text(
        json.dumps(
            {
                "terraria": {"autocreate": 1},
                "manifestType": "terraria",
                "manifestVersion": 1,
            },
            indent=2,
        )
        + "\n",
    )

    manifests = await game.display_manifests()
    assert [manifest.path for manifest in manifests] == sorted([created.path, "ses_9999"])


async def test_create_display_and_update_minecraft_manifest(app: App, tmp_path: Path) -> None:
    game = make_minecraft(app, tmp_path / "minecraft")

    created = await game.create_manifest(
        minecraft_version="1.21.1",
        modloader_type="fabric",
        modloader_version="0.16.0",
        ram=4096,
    )

    assert created.minecraft_version == "1.21.1"
    assert created.modloader_type == "fabric"
    assert created.modloader_version == "0.16.0"
    assert created.ram == 4096
    assert created.java_version > 0
    assert created.jvm_arguments == []

    raw = json.loads(game.get_instance_dir(created.path).joinpath("trident.manifest.json").read_text())
    assert raw["minecraft"]["version"] == "1.21.1"
    assert raw["minecraft"]["modLoader"]["type"] == "fabric"
    assert raw["minecraft"]["modLoader"]["version"] == "0.16.0"
    assert raw["minecraft"]["ram"] == 4096
    assert raw["minecraft"]["javaVersion"] == created.java_version
    assert raw["manifestType"] == "minecraft-java-edition"
    assert raw["manifestVersion"] == 1

    updated = await game.update_manifest(created.path, ram=8192)

    assert updated.ram == 8192
    assert updated.minecraft_version == "1.21.1"
    assert updated.modloader_type == "fabric"
    assert updated.java_version == created.java_version

    manifests = await game.display_manifests()
    assert manifests[0].ram == 8192


async def test_minecraft_rejects_unknown_modloader(app: App, tmp_path: Path) -> None:
    game = make_minecraft(app, tmp_path / "minecraft")

    with pytest.raises(ValueError, match="Modloader type must be one of"):
        await game.create_manifest(
            minecraft_version="1.21.1",
            modloader_type="quilt",
            modloader_version="0.1.0",
            ram=2048,
        )


async def test_tmodloader_manifest_type_is_preserved(app: App, tmp_path: Path) -> None:
    game = make_tmodloader(app, tmp_path / "tmodloader")

    created = await game.create_manifest(steam_app_beta_branch="beta", game_autocreate=1)

    raw = json.loads(game.get_instance_dir(created.path).joinpath("trident.manifest.json").read_text())
    assert raw["manifestType"] == "tmodloader"
    assert raw["terraria"]["autocreate"] == 1
    assert raw["terraria"]["steamAppBetaBranch"] == "beta"

    manifests = await game.display_manifests()
    assert manifests[0].manifest_type == "tmodloader"
    assert manifests[0].steam_app_beta_branch == "beta"

    updated = await game.update_manifest(created.path, game_autocreate=5)
    assert updated.game_autocreate == 5
    assert updated.manifest_type == "tmodloader"
