from __future__ import annotations

import strawberry


@strawberry.type
class ValheimInstance:
    name: str
    container_name: str
    port: int | None
    running: bool
