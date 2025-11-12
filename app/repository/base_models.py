import uuid
from abc import ABC
from datetime import datetime

import sqlalchemy.sql.functions
from sqlmodel import DateTime, Field, SQLModel  # type: ignore

# from sqlmodel._compat import SQLModelConfig
from app.repository.types import TypeId


class Id(SQLModel, ABC):
    id: TypeId = Field(primary_key=True, default_factory=uuid.uuid7)


class CreatedAt(SQLModel, ABC):
    created_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": sqlalchemy.sql.functions.now()},
        nullable=False,
    )


class UpdatedAt(SQLModel, ABC):
    updated_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": sqlalchemy.sql.functions.now(),
            "onupdate": sqlalchemy.sql.functions.now(),
        },
    )


class Enabled(SQLModel, ABC):
    enabled: bool = Field(
        default=True,
        nullable=False,
        sa_column_kwargs={"server_default": sqlalchemy.sql.functions.now()},
    )
