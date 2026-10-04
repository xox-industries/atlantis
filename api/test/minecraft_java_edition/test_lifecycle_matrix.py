from __future__ import annotations

import contextlib
import shutil
from pathlib import Path

import pytest

from test.conftest import ApiUrl
from test.minecraft_java_edition._client import (
    consume_start_subscription,
    consume_stop_subscription,
    execute_graphql,
    wait_for_server_status,
)
from test.minecraft_java_edition._matrix import build_matrix_params
from test.minecraft_java_edition._operations import (
    CREATE_MUTATION,
    LATEST_MODLOADER_QUERY,
)

pytestmark = pytest.mark.asyncio


@pytest.mark.parametrize(
    ("minecraft_version", "modloader_type"),
    build_matrix_params(),
)
async def test_minecraft_java_edition_lifecycle(
    minecraft_version: str,
    modloader_type: str,
    api_url: ApiUrl,
    test_data_dir: Path,
) -> None:
    """Exercise create/start/status lifecycle for one version/modloader combination."""
    latest_result = await execute_graphql(
        api_url,
        LATEST_MODLOADER_QUERY,
        variables={
            "modloaderType": modloader_type,
            "minecraftVersion": minecraft_version,
        },
    )
    modloader_version = latest_result["latestMinecraftJavaEditionModloaderVersion"]
    assert isinstance(modloader_version, str)

    create_result = await execute_graphql(
        api_url,
        CREATE_MUTATION,
        variables={
            "minecraftVersion": minecraft_version,
            "modloaderType": modloader_type,
            "modloaderVersion": modloader_version,
            "ram": 4096,
        },
    )
    path = create_result["createMinecraftJavaEdition"]["path"]

    try:
        port = await consume_start_subscription(api_url, path)
        await wait_for_server_status(port)
    finally:
        with contextlib.suppress(Exception):
            await consume_stop_subscription(api_url, path)

        shutil.rmtree(test_data_dir.joinpath("minecraft-java-edition", path), ignore_errors=True)
