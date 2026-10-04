from __future__ import annotations

from typing import Final

import pytest
from _pytest.mark.structures import ParameterSet
from packaging.version import parse as parse_version

MINECRAFT_VERSIONS: Final[tuple[str, ...]] = (
    "1.8",
    "1.11.2",
    "1.12.2",
    "1.16.5",
    "1.17.1",
    "1.18.2",
    "1.19.4",
    "1.20.6",
    "1.21",
    "1.21.1",
    "1.21.11",
    "26.1",
    "26.1.2",
    "26.3",
)

MODLOADER_TYPES: Final[tuple[str, ...]] = (
    "forge",
    "neoforge",
    "fabric",
)


def build_matrix_params() -> list[ParameterSet]:
    """Return parametrized (minecraft_version, modloader_type) pairs with xfail marks."""
    params: list[ParameterSet] = []
    for version in MINECRAFT_VERSIONS:
        for modloader in MODLOADER_TYPES:
            marks: list[pytest.MarkDecorator] = []
            if modloader == "neoforge" and parse_version(version) < parse_version("1.20.2"):
                marks.append(pytest.mark.xfail(reason="NeoForge requires Minecraft 1.20.2+"))
            elif modloader == "fabric" and parse_version(version) < parse_version("1.14"):
                marks.append(pytest.mark.xfail(reason="Fabric requires Minecraft 1.14+"))
            params.append(pytest.param(version, modloader, marks=marks))
    return params
