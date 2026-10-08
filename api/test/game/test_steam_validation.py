from __future__ import annotations

from pathlib import Path

from src.app import App
from test.game._helpers import (
    RecordingSteam,
    make_palworld,
    make_terraria,
    make_tmodloader,
    make_valheim,
)


async def test_terraria_validate_app_forwards_beta_branch(app: App, tmp_path: Path) -> None:
    steam = RecordingSteam()
    app.steam = steam
    game = make_terraria(app, tmp_path / "terraria")
    created = await game.create_manifest(steam_app_beta_branch="public-beta", game_autocreate=1)

    lines = [line async for line in await game.validate_app(created.path)]

    assert lines == ["ok"]
    assert steam.validate_calls == [
        {
            "app_id": "105600",
            "anonymous": False,
            "platform": "linux",
            "beta_branch": "public-beta",
        },
    ]


async def test_tmodloader_validate_app_forwards_beta_branch(app: App, tmp_path: Path) -> None:
    steam = RecordingSteam()
    app.steam = steam
    game = make_tmodloader(app, tmp_path / "tmodloader")
    created = await game.create_manifest(steam_app_beta_branch="beta", game_autocreate=1)

    lines = [line async for line in await game.validate_app(created.path)]

    assert lines == ["ok"]
    assert steam.validate_calls == [
        {
            "app_id": "1281930",
            "anonymous": False,
            "platform": "linux",
            "beta_branch": "beta",
        },
    ]


async def test_palworld_validate_app_uses_anonymous_windows(app: App, tmp_path: Path) -> None:
    steam = RecordingSteam()
    app.steam = steam
    game = make_palworld(app, tmp_path / "palworld")
    created = await game.create_manifest()

    lines = [line async for line in await game.validate_app(created.path)]

    assert lines == ["ok"]
    assert steam.validate_calls == [
        {
            "app_id": "2394010",
            "anonymous": True,
            "platform": "windows",
            "beta_branch": None,
        },
    ]


async def test_palworld_validate_app_forwards_beta_branch(app: App, tmp_path: Path) -> None:
    steam = RecordingSteam()
    app.steam = steam
    game = make_palworld(app, tmp_path / "palworld")
    created = await game.create_manifest(steam_app_beta_branch="public-beta")

    lines = [line async for line in await game.validate_app(created.path)]

    assert lines == ["ok"]
    assert steam.validate_calls == [
        {
            "app_id": "2394010",
            "anonymous": True,
            "platform": "windows",
            "beta_branch": "public-beta",
        },
    ]


async def test_valheim_validate_app_uses_anonymous_linux(app: App, tmp_path: Path) -> None:
    steam = RecordingSteam()
    app.steam = steam
    game = make_valheim(app, tmp_path / "valheim")
    created = await game.create_manifest()

    lines = [line async for line in await game.validate_app(created.path)]

    assert lines == ["ok"]
    assert steam.validate_calls == [
        {
            "app_id": "896660",
            "anonymous": True,
            "platform": "linux",
            "beta_branch": None,
        },
    ]


async def test_valheim_validate_app_forwards_beta_branch(app: App, tmp_path: Path) -> None:
    steam = RecordingSteam()
    app.steam = steam
    game = make_valheim(app, tmp_path / "valheim")
    created = await game.create_manifest(steam_app_beta_branch="beta")

    lines = [line async for line in await game.validate_app(created.path)]

    assert lines == ["ok"]
    assert steam.validate_calls == [
        {
            "app_id": "896660",
            "anonymous": True,
            "platform": "linux",
            "beta_branch": "beta",
        },
    ]
