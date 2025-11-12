from abc import ABC
from collections.abc import Callable, Coroutine
from enum import StrEnum
from typing import Any, ClassVar, final

from fastapi import Request, Response
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from requests.structures import CaseInsensitiveDict

HandlerFunc = Callable[[Request, "ErrBase[Any]"], Coroutine[Any, Any, Response]]
handler_dict: dict[int | type[Exception], HandlerFunc] = {}


class ErrBase[C: StrEnum](Exception, ABC):
    default_status_code: ClassVar[int] = 400
    """When a class extends this `ErrBase`, then `__init_subclass__` will be called,
    which will set this default status code value vie updating the class property"""

    def __init__(self, code: C, status: int | None = None, detail: Any = None, headers: dict[str, str] | None = None):
        self.code = code
        self.status = status or self.default_status_code
        """
        Note that if status is not passed, we don't want the status to be 400, rather we need to set
        the status to be the default status code for that child class, that's why we don't pass 400 
        directly and pass None, we can check if argument is None and set the default status.
        """
        self.detail = detail
        self.headers = CaseInsensitiveDict(headers or {})
        """
        https://www.hackerone.com/blog/python-pitfalls-perils-using-lists-and-dicts-default-arguments
        """

    def __init_subclass__(cls, **kwargs: Any):
        """
        Because this is an error base, the default status is 400. If the default status for some
        other error class is different, pass the status code after extending from this class .
        e.g. for authorization default can be 401 unauthorized.
        """
        super().__init_subclass__(**kwargs)
        handler_dict[cls] = cls.handle_error_response

    @staticmethod
    async def handle_error_response(_: Request, exc: "ErrBase[C]") -> Response:
        """In case a handler needs to set headers, override this method."""
        return exc.create_json_response()

    @final
    def create_json_response(self) -> Response:
        content = jsonable_encoder(self, exclude={"status", "headers"}, exclude_none=True)
        return JSONResponse(content, self.status, self.headers)
