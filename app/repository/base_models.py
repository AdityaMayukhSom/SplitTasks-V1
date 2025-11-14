import uuid
from datetime import datetime

import sqlalchemy.sql.functions as saf
from sqlmodel import (
    DateTime,
    Field as SQLField,  # type: ignore
    SQLModel,
    true,
)

from app.repository.types import TypeId


class Id(SQLModel):
    id: TypeId = SQLField(
        primary_key=True,
        default_factory=uuid.uuid7,
    )


class CreatedAt(SQLModel):
    created_at: datetime | None = SQLField(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": saf.now(),
        },
    )


class UpdatedAt(SQLModel):
    updated_at: datetime | None = SQLField(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": saf.now(),
            "onupdate": saf.now(),
        },
    )


class Enabled(SQLModel):
    enabled: bool = SQLField(
        default=True,
        nullable=False,
        sa_column_kwargs={
            "server_default": true(),
        },
    )
