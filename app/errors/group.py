from enum import StrEnum, auto

from app.errors.conf import ErrBase


class CodeGroupAuth(StrEnum):
    NOT_MEMBER_OF_GROUP = auto()
    NOT_AN_ADMIN = auto()


class ErrGroupAuth(ErrBase[CodeGroupAuth]):
    default_status_code = 401


class CodeGroupInvite(StrEnum):
    ALREADY_MEMBER = auto()
    INVITEE_DOES_NOT_EXIST = auto()
    GROUP_DOES_NOT_EXIST = auto()
    ALREADY_PENDING_REQUEST = auto()
    UNABLE_TO_INVITE = auto()


class ErrGroupInvite(ErrBase[CodeGroupInvite]):
    default_status_code = 400
