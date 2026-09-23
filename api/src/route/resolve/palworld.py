import strawberry


@strawberry.type
class PalworldInstance:
    name: str
    running: bool
    port: int | None = None
