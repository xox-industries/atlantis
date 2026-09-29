from __future__ import annotations

import contextlib
import shutil
from pathlib import Path

import pytest

from test.conftest import ApiUrl
from test.minecraft_java_edition._helpers import (
    CREATE_MUTATION,
    LATEST_MODLOADER_QUERY,
    STOP_MUTATION,
    build_matrix_params,
    consume_start_subscription,
    execute_graphql,
    wait_for_server_status,
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
    path = f"{minecraft_version}/{modloader_type}"
    test_dir = test_data_dir.joinpath("minecraft-java-edition", path)

    shutil.rmtree(test_dir, ignore_errors=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    try:
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
                "path": path,
                "minecraftVersion": minecraft_version,
                "modloaderType": modloader_type,
                "modloaderVersion": modloader_version,
                "ram": 4096,
            },
        )
        assert create_result["createMinecraftJavaEdition"]["path"] == path

        port = await consume_start_subscription(api_url, path)
        await wait_for_server_status(port)
    finally:
        with contextlib.suppress(Exception):
            await execute_graphql(api_url, STOP_MUTATION, variables={"path": path})
        shutil.rmtree(test_dir, ignore_errors=True)
