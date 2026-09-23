from collections.abc import Callable
from typing import Literal

from fastapi import UploadFile
from strawberry import Schema
from strawberry.file_uploads import UploadDefinition
from strawberry.schema.base import BaseSchema

from src.app import App
from src.route.context import AppContext
from src.route.mutate import MutationSchema
from src.route.query import QuerySchema
from src.route.subscribe import SubscribeSchema


def create_context(app: App, /, env: Literal["production", "development"]) -> Callable[..., AppContext]:
    return lambda: AppContext(app, env=env)


def create_schema() -> BaseSchema:
    return Schema(
        query=QuerySchema,
        mutation=MutationSchema,
        subscription=SubscribeSchema,
        scalar_overrides={UploadFile: UploadDefinition},
    )
