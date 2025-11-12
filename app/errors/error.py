from enum import StrEnum, auto
from typing import override

from fastapi import Request, Response

from app.errors.conf import ErrBase

# ------------------------------------------------------------------------------


class CodeGroupAuth(StrEnum):
    NOT_MEMBER_OF_GROUP = auto()
    NOT_AN_ADMIN = auto()


class ErrGroupAuth(ErrBase[CodeGroupAuth]):
    default_status_code = 401


# ------------------------------------------------------------------------------


class CodeGroupInvite(StrEnum):
    INVITEE_ALREADY_MEMBER = auto()
    ALREADY_PENDING_REQUEST = auto()
    UNABLE_TO_INVITE = auto()


class ErrGroupInvite(ErrBase[CodeGroupInvite]):
    default_status_code = 400


# ------------------------------------------------------------------------------


class CodeItemNotFound(StrEnum):
    USER_NOT_FOUND = auto()
    GROUP_NOT_FOUND = auto()


class ErrItemNotFound(ErrBase[CodeItemNotFound]):
    default_status_code = 404


# ------------------------------------------------------------------------------


class CodeUserExists(StrEnum):
    EMAIL_EXISTS = auto()
    MOBILE_EXISTS = auto()


class ErrUserExists(ErrBase[CodeUserExists]):
    default_status_code = 409


# ------------------------------------------------------------------------------


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


# ------------------------------------------------------------------------------
