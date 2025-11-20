from enum import StrEnum, auto


class PaymentStatus(StrEnum):
    CANCELLED = auto()
    DECLINED = auto()
    REQUESTED = auto()
    SETTLED = auto()


class TaskStatus(StrEnum):
    CANCELLED = auto()
    DECLINED = auto()
    FINISHED = auto()
    PENDING = auto()


class MembershipStatus(StrEnum):
    PENDING = auto()
    ALTERNATE = auto()
    """represents user is a member of the same group via another account"""
    ACTIVE = auto()
    DECLINED = auto()
    CANCELLED = auto()
    REMOVED = auto()
    EXITED = auto()
