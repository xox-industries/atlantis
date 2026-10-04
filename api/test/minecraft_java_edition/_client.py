from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Final

import httpx
import websockets
from mcstatus import JavaServer
from websockets.typing import Subprotocol

from test.minecraft_java_edition._operations import START_SUBSCRIPTION, STOP_SUBSCRIPTION

if TYPE_CHECKING:
    from test.conftest import ApiUrl


_GRAPHQL_TRANSPORT_WS: Final[str] = "graphql-transport-ws"
_CONNECTION_ACK: Final[str] = "connection_ack"
_CONNECTION_INIT: Final[str] = "connection_init"
_NEXT: Final[str] = "next"
_COMPLETE: Final[str] = "complete"
_ERROR: Final[str] = "error"
_SUBSCRIBE: Final[str] = "subscribe"


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


async def _subscribe(
    api_url: ApiUrl,
    query: str,
    data_field: str,
    variables: dict[str, Any] | None = None,
    *,
    timeout_seconds: float = 300.0,
) -> AsyncGenerator[str]:
    """Run a single GraphQL subscription and yield each ``data.<data_field>`` string."""
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
                    "id": "sub",
                    "payload": {
                        "query": query,
                        "variables": variables or {},
                    },
                },
            ),
        )

        while True:
            remaining = deadline - asyncio.get_running_loop().time()
            if remaining <= 0:
                msg = "Subscription timed out before completing"
                raise TimeoutError(msg)

            raw = await asyncio.wait_for(websocket.recv(), timeout=remaining)
            message = json.loads(raw)
            message_type = message.get("type")

            if message_type == _ERROR:
                raise GraphQLError(message.get("payload", message))
            if message_type == _COMPLETE:
                return
            if message_type != _NEXT:
                continue

            payload = message.get("payload", {})
            if "errors" in payload:
                raise GraphQLError(payload["errors"])

            text = payload.get("data", {}).get(data_field)
            if isinstance(text, str):
                yield text


async def consume_start_subscription(
    api_url: ApiUrl,
    path: str,
    *,
    timeout_seconds: float = 300.0,
) -> int:
    """Subscribe to the start subscription and return the port once the server is up."""
    async for text in _subscribe(
        api_url,
        START_SUBSCRIPTION,
        "startMinecraftJavaEdition",
        {"path": path},
        timeout_seconds=timeout_seconds,
    ):
        print(text)
        if text.startswith("Started on port"):
            return int(text.removeprefix("Started on port").strip())

    msg = "Subscription ended without yielding a port"
    raise GraphQLError(msg)


async def consume_stop_subscription(
    api_url: ApiUrl,
    path: str,
    *,
    timeout_seconds: float = 300.0,
) -> list[str]:
    """Subscribe to the stop subscription and return all streamed output lines."""
    return [
        text
        async for text in _subscribe(
            api_url,
            STOP_SUBSCRIPTION,
            "stopMinecraftJavaEdition",
            {"path": path},
            timeout_seconds=timeout_seconds,
        )
    ]


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
