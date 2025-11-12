from enum import StrEnum, auto

from app.errors.conf import ErrBase


class CodeUserExists(StrEnum):
    EMAIL_EXISTS = auto()
    MOBILE_EXISTS = auto()


class ErrUserExists(ErrBase[CodeUserExists]):
    default_status_code = 409
