from __future__ import annotations

import pytest

from src.app import App


@pytest.fixture
def app() -> App:
    """Return a bare App whose docker/steam collaborators are replaced per test."""
    return App()
