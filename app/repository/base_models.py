import uuid
from abc import ABC
from datetime import datetime

from sqlalchemy import text
from sqlmodel import DateTime, Field, func

from app.repository.types import TypeId


class _Id(ABC):
    id: TypeId = Field(primary_key=True, default_factory=uuid.uuid7)


class _CreatedAt(ABC):
    created_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )


class _UpdatedAt(ABC):
    updated_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "onupdate": lambda: func.now()},
    )


class _Enabled(ABC):
    enabled: bool = Field(
        default=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("TRUE")},
    )
