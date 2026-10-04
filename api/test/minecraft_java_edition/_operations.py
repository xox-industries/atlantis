from __future__ import annotations

from typing import Final

LATEST_MODLOADER_QUERY: Final[str] = """
query LatestModloaderVersion($modloaderType: String!, $minecraftVersion: String!) {
    latestMinecraftJavaEditionModloaderVersion(
        modloaderType: $modloaderType
        minecraftVersion: $minecraftVersion
    )
}
"""

CREATE_MUTATION: Final[str] = """
mutation CreateMinecraftJavaEdition(
    $minecraftVersion: String!
    $modloaderType: String!
    $modloaderVersion: String!
    $ram: Int!
) {
    createMinecraftJavaEdition(
        minecraftVersion: $minecraftVersion
        modloaderType: $modloaderType
        modloaderVersion: $modloaderVersion
        ram: $ram
    ) {
        path
    }
}
"""

START_SUBSCRIPTION: Final[str] = """
subscription StartMinecraftJavaEdition($path: String!) {
    startMinecraftJavaEdition(path: $path)
}
"""

STOP_SUBSCRIPTION: Final[str] = """
subscription StopMinecraftJavaEdition($path: String!) {
    stopMinecraftJavaEdition(path: $path)
}
"""
