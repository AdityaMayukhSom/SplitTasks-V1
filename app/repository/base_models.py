import uuid
from datetime import datetime

import sqlalchemy.sql.functions as saf
from sqlmodel import (
    DateTime,
    Field,  # type: ignore
    SQLModel,
    true,
)

from app.repository.types import TypeId


class Id(SQLModel):
    id: TypeId = Field(
        primary_key=True,
        default_factory=uuid.uuid7,
    )


class CreatedAt(SQLModel):
    created_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": saf.now(),
        },
    )


class UpdatedAt(SQLModel):
    updated_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": saf.now(),
            "onupdate": saf.now(),
        },
    )


class Enabled(SQLModel):
    enabled: bool = Field(
        default=True,
        nullable=False,
        sa_column_kwargs={
            "server_default": true(),
        },
    )
