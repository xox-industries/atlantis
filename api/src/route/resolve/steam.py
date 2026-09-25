import strawberry


@strawberry.type
class SteamAccount:
    username: str | None = None
