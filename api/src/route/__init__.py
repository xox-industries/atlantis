from collections.abc import Callable
from typing import Literal

from fastapi import UploadFile
from strawberry import Schema
from strawberry.fastapi import BaseContext
from strawberry.file_uploads import UploadDefinition
from strawberry.schema.base import BaseSchema

from src.app import App
from src.route.mutate import MutationSchema
from src.route.query import QuerySchema


class AppContext(BaseContext):
    def __init__(self, app: App, /, env: Literal["production", "development"]) -> None:
        super().__init__()
        self.app = app
        self.env = env


def create_context(app: App, /, env: Literal["production", "development"]) -> Callable[..., AppContext]:
    return lambda: AppContext(app, env=env)


def create_schema() -> BaseSchema:
    return Schema(
        query=QuerySchema,
        mutation=MutationSchema,
        scalar_overrides={UploadFile: UploadDefinition},
    )
