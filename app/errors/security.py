from enum import StrEnum, auto
from typing import override

from fastapi import Request, Response

from app.errors.conf import ErrBase


class CodeOAuth(StrEnum):
    INVALID_REQUEST = auto()
    INVALID_CLIENT = auto()
    INVALID_GRANT = auto()
    INVALID_SCOPE = auto()
    UNAUTHORIZED_CLIENT = auto()
    UNSUPPORTED_GRANT_TYPE = auto()


class ErrOAuth(ErrBase[CodeOAuth]):
    default_status_code = 401

    @override
    @staticmethod
    async def handle_error_response(_: Request, exc: ErrBase[CodeOAuth]) -> Response:
        exc.headers["WWW-Authenticate"] = "Bearer"
        return exc.create_json_response()
