from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urljoin

import httpx
import pytest


@dataclass(frozen=True)
class ApiUrl:
    base: str
    graphql: str
    health: str
    ws: str


_ATLANTIS_TEST_DATA_DIR = Path(__file__).resolve().parents[2].joinpath(".atlantis")


@pytest.fixture
def api_url() -> ApiUrl:
    """Return URLs for the running Atlantis API and fail fast if it is not healthy."""
    base = "http://127.0.0.1:5000"
    ws_base = "ws://127.0.0.1:5000"
    graphql = urljoin(base, "/graphql")
    health = urljoin(base, "/health")
    ws = urljoin(ws_base, "/graphql")

    try:
        response = httpx.get(health, timeout=5)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        msg = f"Atlantis API is not reachable at {health}: {exc}"
        raise RuntimeError(msg) from exc

    return ApiUrl(base=base, graphql=graphql, health=health, ws=ws)


@pytest.fixture
def test_data_dir() -> Path:
    return _ATLANTIS_TEST_DATA_DIR
