from enum import StrEnum, auto
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from app.errors.conf import ErrBase


class CodeOAuth(StrEnum):
    INVALID_REQUEST = auto()
    INVALID_CLIENT = auto()
    INVALID_GRANT = auto()
    INVALID_SCOPE = auto()
    UNAUTHORIZED_CLIENT = auto()
    UNSUPPORTED_GRANT_TYPE = auto()


class ErrOAuth(ErrBase[CodeOAuth]):
    @staticmethod
    async def handle_error_response(_: Request, exc: ErrBase[CodeOAuth]) -> Response:
        sc = exc.status if exc.status is not None else status.HTTP_401_UNAUTHORIZED
        return JSONResponse(status_code=sc, content=exc, headers={"WWW-Authenticate": "Bearer"})
