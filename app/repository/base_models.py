import uuid
from abc import ABC
from datetime import datetime

from pydantic import BaseModel, ConfigDict
from sqlalchemy import text
from sqlmodel import (
    DateTime,
    Field,  # type: ignore
    SQLModel,
    func,
)

from app.repository.types import TypeId


class Validated(ABC, BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        validate_default=True,
    )


class Id(ABC, SQLModel):
    id: TypeId = Field(primary_key=True, default_factory=uuid.uuid7)


class CreatedAt(ABC, SQLModel):
    created_at: datetime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now()},
        nullable=False,
    )


class UpdatedAt(ABC, SQLModel):
    updated_at: datetime | None = Field(
        default=None,
        nullable=False,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={"server_default": func.now(), "onupdate": lambda: func.now()},
    )


class Enabled(ABC, SQLModel):
    enabled: bool = Field(
        default=True,
        nullable=False,
        sa_column_kwargs={"server_default": text("TRUE")},
    )
