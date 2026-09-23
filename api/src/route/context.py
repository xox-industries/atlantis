from __future__ import annotations

from typing import Literal

from strawberry.fastapi import BaseContext

from src.app import App


class AppContext(BaseContext):
    def __init__(self, app: App, /, env: Literal["production", "development"]) -> None:
        super().__init__()
        self.app = app
        self.env = env
