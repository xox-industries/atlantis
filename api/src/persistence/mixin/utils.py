import asyncio
import inspect
import threading
from collections.abc import Awaitable, Callable, Generator
from typing import Any, overload


class LazyAwaitable[T]:
    @overload
    def __init__(self, fn: Awaitable[T], /) -> None: ...
    @overload
    def __init__(self, fn: Callable[[], T], /) -> None: ...
    @overload
    def __init__(self, fn: Callable[[], Awaitable[T]], /) -> None: ...

    def __init__(self, fn: Any, /) -> None:
        self._fn = fn
        self._task: asyncio.Task[T] | None = None
        self._lock = threading.Lock()

    async def _run(self) -> T:
        if callable(self._fn):
            result = self._fn()
            if inspect.isawaitable(result):
                return await result

            return result

        if inspect.isawaitable(self._fn):
            return await self._fn

        raise TypeError

    def __await__(self) -> Generator[Any, None, T]:
        with self._lock:
            if self._task is None:
                self._task = asyncio.create_task(self._run())

        return self._task.__await__()


class InsertConstructor:
    def __init__(self, initial: list[Any] | None = None, /) -> None:
        self._pairs: dict[str, Any] = {}
        self._values: list[Any] = initial or []
        self._initial = len(self._values)

    def add(self, key: str, value: Any, /) -> None:  # noqa: ANN401
        self._pairs[key] = value
        self._values.append(value)

    def query(self, template: str, /) -> str:
        columns = ", ".join(self._pairs.keys())
        placeholders = ", ".join(f"${i}" for i in range(self._initial + 1, self._initial + len(self._pairs) + 1))

        return template.replace("$COLUMNS", columns).replace("$VALUES", placeholders)

    @property
    def values(self) -> tuple[Any]:
        return tuple(self._values)


class UpdateConstructor:
    def __init__(self, initial: list[Any] | None = None, /) -> None:
        self._pairs: dict[str, Any] = {}
        self._values: list[Any] = initial or []
        self._initial = len(self._values)

    def add(self, key: str, value: Any, /) -> None:  # noqa: ANN401
        self._pairs[key] = value
        self._values.append(value)

    def query(self, template: str, /) -> str:
        set_clauses = [f"{key} = ${i}" for i, key in enumerate(self._pairs.keys(), start=self._initial + 1)]
        return template.replace("$SET_CLAUSES", ", ".join(set_clauses))

    @property
    def values(self) -> tuple[Any]:
        return tuple(self._values)
