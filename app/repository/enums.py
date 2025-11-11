from enum import StrEnum, auto


class PaymentStatus(StrEnum):
    CANCELLED = auto()
    DECLINED = auto()
    REQUESTED = auto()
    SETTLED = auto()


class SplitType(StrEnum):
    EQUAL = auto()
    EXACT = auto()
    PERCENTAGE = auto()


class TaskStatus(StrEnum):
    CANCELLED = auto()
    DECLINED = auto()
    FINISHED = auto()
    PENDING = auto()


class MembershipStatus(StrEnum):
    REQUESTED = auto()
    CANCELLED = auto()
    DECLINED = auto()
    ACCEPTED = auto()
    EXITED = auto()
    REMOVED = auto()
