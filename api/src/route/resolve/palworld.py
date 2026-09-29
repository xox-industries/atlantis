import strawberry


@strawberry.type
class PalworldInstance:
    name: str
    container_name: str
    running: bool
    port: int | None = None
