from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING, Any, Final

import httpx
import pytest
import websockets
from _pytest.mark.structures import ParameterSet
from mcstatus import JavaServer
from packaging.version import parse as parse_version
from websockets.typing import Subprotocol

if TYPE_CHECKING:
    from test.conftest import ApiUrl


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
    $path: String!
    $minecraftVersion: String!
    $modloaderType: String!
    $modloaderVersion: String!
    $ram: Int!
) {
    createMinecraftJavaEdition(
        path: $path
        minecraftVersion: $minecraftVersion
        modloaderType: $modloaderType
        modloaderVersion: $modloaderVersion
        ram: $ram
    ) {
        path
    }
}
"""

STOP_MUTATION: Final[str] = """
mutation StopMinecraftJavaEdition($path: String!) {
    stopMinecraftJavaEdition(path: $path) {
        path
    }
}
"""

START_SUBSCRIPTION: Final[str] = """
subscription StartMinecraftJavaEdition($path: String!) {
    startMinecraftJavaEdition(path: $path)
}
"""

_GRAPHQL_TRANSPORT_WS = "graphql-transport-ws"
_CONNECTION_ACK = "connection_ack"
_CONNECTION_INIT = "connection_init"
_NEXT = "next"
_COMPLETE = "complete"
_ERROR = "error"
_SUBSCRIBE = "subscribe"


class GraphQLError(RuntimeError):
    """Raised when a GraphQL operation returns errors or the transport fails."""


async def execute_graphql(
    api_url: ApiUrl,
    query: str,
    *,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Execute a GraphQL query or mutation against the running API."""
    payload: dict[str, Any] = {"query": query}
    if variables is not None:
        payload["variables"] = variables

    async with httpx.AsyncClient(timeout=300) as client:
        response = await client.post(api_url.graphql, json=payload)
        response.raise_for_status()
        data = response.json()

    if "errors" in data:
        raise GraphQLError(data["errors"])

    return data.get("data", {})


async def consume_start_subscription(
    api_url: ApiUrl,
    path: str,
    *,
    timeout_seconds: float = 300.0,
) -> int:
    """Subscribe to the start subscription and return the port once the server is up."""
    deadline = asyncio.get_running_loop().time() + timeout_seconds

    async with websockets.connect(
        api_url.ws,
        subprotocols=[Subprotocol(_GRAPHQL_TRANSPORT_WS)],
        open_timeout=10,
        close_timeout=10,
    ) as websocket:
        await websocket.send(json.dumps({"type": _CONNECTION_INIT}))
        init_message = await asyncio.wait_for(websocket.recv(), timeout=10)
        if json.loads(init_message)["type"] != _CONNECTION_ACK:
            msg = "GraphQL WebSocket connection was not acknowledged"
            raise GraphQLError(msg)

        await websocket.send(
            json.dumps(
                {
                    "type": _SUBSCRIBE,
                    "id": "start-sub",
                    "payload": {
                        "query": START_SUBSCRIPTION,
                        "variables": {"path": path},
                    },
                },
            ),
        )

        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                msg = "Start subscription timed out before yielding a port"
                raise TimeoutError(msg)

            raw = await asyncio.wait_for(websocket.recv(), timeout=remaining)
            message = json.loads(raw)
            message_type = message.get("type")

            if message_type == _ERROR:
                raise GraphQLError(message.get("payload", message))
            if message_type == _COMPLETE:
                msg = "Subscription ended without yielding a port"
                raise GraphQLError(msg)
            if message_type != _NEXT:
                continue

            payload = message.get("payload", {})
            if "errors" in payload:
                raise GraphQLError(payload["errors"])

            text = payload.get("data", {}).get("startMinecraftJavaEdition")
            if not isinstance(text, str):
                continue
            print(text)
            if text.startswith("Started on port"):
                return int(text.removeprefix("Started on port").strip())


async def wait_for_server_status(
    port: int,
    *,
    timeout_seconds: float = 300.0,
    sleep_seconds: float = 1.0,
) -> None:
    """Ping a Minecraft server until it responds or the timeout expires."""
    deadline = asyncio.get_running_loop().time() + timeout_seconds
    last_error: Exception | None = None
    while True:
        try:
            server = await JavaServer.async_lookup(f"127.0.0.1:{port}")
            await server.async_status()
        except (OSError, TimeoutError) as exc:
            last_error = exc
            if asyncio.get_running_loop().time() >= deadline:
                msg = f"Minecraft server on port {port} did not become reachable within {timeout_seconds}s"
                raise TimeoutError(msg) from last_error
            await asyncio.sleep(sleep_seconds)
        else:
            return


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
