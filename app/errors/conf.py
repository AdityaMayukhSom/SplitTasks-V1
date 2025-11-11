from abc import ABC, abstractmethod
from collections.abc import Callable, Coroutine
from enum import StrEnum
from typing import Annotated, Any

from fastapi import Request, Response
from pydantic import Field


HandlerFunc = Callable[[Request, "ErrBase[Any]"], Coroutine[Any, Any, Response]]
handler_dict: dict[int | type[Exception], HandlerFunc] = {}


class ErrBase[C: StrEnum](ABC, Exception):
    code: C
    status: Annotated[int | None, Field(exclude=True, ge=100, lt=600)] = None
    detail: Annotated[str | None, Field(exclude_if=lambda d: d is None)] = None

    @staticmethod
    @abstractmethod
    async def handle_error_response(_: Request, exc: "ErrBase[C]") -> Response:
        raise NotImplementedError

    def __init_subclass__(cls, **kwargs: Any):
        super().__init_subclass__(**kwargs)
        if not getattr(cls.handle_error_response, "__isabstractmethod__", False):
            handler_dict[cls] = cls.handle_error_response
