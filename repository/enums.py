from enum import Enum


class PaymentStatus(str, Enum):
    CANCELLED = "Cancelled"
    DECLINED = "Declined"
    REQUESTED = "Requested"
    SETTLED = "Settled"


class SplitType(str, Enum):
    EQUAL = "Equal"
    EXACT = "Exact"
    PERCENTAGE = "Percentage"


class TaskStatus(str, Enum):
    CANCELLED = "Cancelled"
    DECLINED = "Declined"
    FINISHED = "Finished"
    PENDING = "Pending"
