import enum
from collections.abc import AsyncGenerator

import strawberry
from strawberry.types import Info

from src.route.context import AppContext


@strawberry.enum
class SteamPlatform(enum.Enum):
    WINDOWS = "windows"
    LINUX = "linux"


@strawberry.type
class SubscribeSteamType:
    @strawberry.subscription
    async def steam_login(
        self,
        username: str,
        password: str,
        info: Info["AppContext"],
        *,
        code: str | None = None,
    ) -> AsyncGenerator[str]:
        steam = info.context.app.steam
        return await steam.login(username=username, password=password, code=code)

    @strawberry.subscription
    async def steam_validate_app(
        self,
        app_id: str,
        info: Info["AppContext"],
        *,
        anonymous: bool = False,
        platform: SteamPlatform = SteamPlatform.LINUX,
    ) -> AsyncGenerator[str]:
        steam = info.context.app.steam
        return await steam.validate_app(
            app_id=app_id,
            anonymous=anonymous,
            platform=platform.value,
        )
