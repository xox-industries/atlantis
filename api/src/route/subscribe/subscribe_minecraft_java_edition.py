from __future__ import annotations

from collections.abc import AsyncGenerator

import strawberry
from strawberry.types import Info

from src.route.context import AppContext


@strawberry.type
class SubscribeMinecraftJavaEditionType:
    @strawberry.subscription
    async def start_minecraft_java_edition(
        self,
        path: str,
        info: Info[AppContext],
    ) -> AsyncGenerator[str]:
        return info.context.app.minecraft_java_edition.start(path)
