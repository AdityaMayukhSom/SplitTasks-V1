from enum import StrEnum, auto

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

from app.errors.conf import ErrBase


class CodeGroupAuth(StrEnum):
    NOT_MEMBER_OF_GROUP = auto()
    NOT_AN_ADMIN = auto()


class ErrGroupAuth(ErrBase[CodeGroupAuth]):
    @staticmethod
    async def handle_error_response(_: Request, exc: ErrBase[CodeGroupAuth]) -> Response:
        sc = exc.status if exc.status is not None else status.HTTP_401_UNAUTHORIZED
        return JSONResponse(status_code=sc, content=exc)


class CodeGroupInvite(StrEnum):
    ALREADY_MEMBER = auto()
    INVITEE_DOES_NOT_EXIST = auto()
    GROUP_DOES_NOT_EXIST = auto()
    ALREADY_PENDING_REQUEST = auto()
    UNABLE_TO_INVITE = auto()


class ErrGroupInvite(ErrBase[CodeGroupInvite]):
    @staticmethod
    async def handle_error_response(_: Request, exc: ErrBase[CodeGroupInvite]) -> Response:
        sc = exc.status if exc.status is not None else status.HTTP_400_BAD_REQUEST
        return JSONResponse(status_code=sc, content=exc)
