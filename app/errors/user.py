from enum import StrEnum, auto
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from app.errors.conf import ErrBase


class CodeUserExists(StrEnum):
    EMAIL_EXISTS = auto()
    MOBILE_EXISTS = auto()


class ErrUserExists(ErrBase[CodeUserExists]):
    @staticmethod
    async def handle_error_response(_: Request, exc: ErrBase[CodeUserExists]) -> Response:
        sc = exc.status if exc.status is not None else status.HTTP_409_CONFLICT
        return JSONResponse(status_code=sc, content=exc)
