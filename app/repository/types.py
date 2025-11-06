import uuid
from datetime import date
from decimal import Decimal
from typing import Annotated

from sqlmodel import Field, Date

# https://stackoverflow.com/questions/224462/storing-money-in-a-decimal-column-what-precision-and-scale
TypeMoney = Annotated[Decimal, Field(ge=0.0, default=0.0, nullable=False, max_digits=13, decimal_places=4)]

TypeDOB = Annotated[date | None, Field(default=None, nullable=True, sa_type=Date())]
TypeId = uuid.UUID


def id_to_str(identifier: TypeId) -> str:
    return identifier.hex


def str_to_id(s: str) -> TypeId:
    return uuid.UUID(s)
