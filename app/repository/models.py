from datetime import datetime
from typing import Annotated

from fastapi import Depends
from pydantic import EmailStr, HttpUrl
from pydantic_extra_types.currency_code import Currency
from sqlalchemy import Engine
from sqlmodel import DateTime, Field, Relationship, SQLModel, create_engine, AutoString

from app.config.vars import DBVarsDep
from app.repository.base_models import _Id, _CreatedAt, _UpdatedAt, _Enabled, _Validated
from app.repository.enums import SplitType, TaskStatus, MembershipStatus
from app.repository.types import TypeMoney, TypeDOB, TypeId, TypeMobile


class Account(_Id, _CreatedAt, _UpdatedAt, _Enabled, SQLModel, table=True):
    user_id: TypeId = Field(foreign_key="user.id", index=True)
    group_id: TypeId = Field(foreign_key="group.id", index=True)
    balance: TypeMoney
    membership_status: MembershipStatus = Field(default=MembershipStatus.REQUESTED)


class User(_Validated, _Id, _CreatedAt, _UpdatedAt, _Enabled, SQLModel, table=True):
    name: str | None = Field(default=None)
    email: EmailStr | None = Field(unique=True, index=True, nullable=True)
    mobile: TypeMobile | None = Field(unique=True, index=True, nullable=True)
    password_hash: str
    dob: TypeDOB
    groups: list["Group"] = Relationship(back_populates="users", link_model=Account)

    assigned_tasks: list["Task"] = Relationship(
        back_populates="assigner",
        sa_relationship_kwargs={
            "foreign_keys": "Task.assigner_id",
        },
    )

    received_tasks: list["Task"] = Relationship(
        back_populates="assignee",
        sa_relationship_kwargs={
            "foreign_keys": "Task.assignee_id",
        },
    )


class Group(_Validated, _Id, _CreatedAt, _Enabled, SQLModel, table=True):
    name: str = Field(min_length=1)
    description: str | None = Field(default=None)
    currency: Currency
    display_image: HttpUrl | None = Field(default=None, sa_type=AutoString)
    creator_id: TypeId = Field(foreign_key="user.id")
    admin_id: TypeId = Field(foreign_key="user.id")
    can_users_invite: bool = Field(default=False)
    can_users_edit_info: bool = Field(default=False)
    users: list["User"] = Relationship(back_populates="groups", link_model=Account)
    expenses: list["Expense"] = Relationship(back_populates="group")


class Task(_Id, _CreatedAt, _UpdatedAt, SQLModel, table=True):
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    title: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)
    deadline: datetime = Field(sa_type=DateTime(timezone=True))

    # Reference: https://github.com/fastapi/sqlmodel/discussions/1038
    assignee_id: TypeId = Field(foreign_key="user.id")
    assignee: "User" = Relationship(
        back_populates="received_tasks",
        sa_relationship_kwargs={
            "foreign_keys": "Task.assignee_id",
        },
    )

    assigner_id: TypeId = Field(foreign_key="user.id")
    assigner: "User" = Relationship(
        back_populates="assigned_tasks",
        sa_relationship_kwargs={
            "foreign_keys": "Task.assigner_id",
        },
    )


class Expense(_Id, _CreatedAt, _UpdatedAt, SQLModel, table=True):
    payee_id: TypeId = Field(foreign_key="user.id")
    group_id: TypeId = Field(foreign_key="group.id")
    group: "Group" = Relationship(back_populates="expenses")
    amount: TypeMoney
    split_type: SplitType = Field(default=SplitType.EQUAL)
    splits: list["Split"] = Relationship(back_populates="expense")
    images: list["ExpenseImage"] = Relationship(back_populates="expense")


class ExpenseImage(_Id, SQLModel, table=True):
    uploaded_by: TypeId = Field(foreign_key="user.id")
    expense_id: TypeId = Field(foreign_key="expense.id", index=True)
    expense: Expense = Relationship(back_populates="images")
    permalink: HttpUrl = Field(sa_type=AutoString)


class Split(SQLModel, table=True):
    user_id: TypeId = Field(foreign_key="user.id", primary_key=True)
    expense_id: TypeId = Field(foreign_key="expense.id", primary_key=True)
    expense: Expense = Relationship(back_populates="splits")
    amount: TypeMoney


def get_engine(db_vars: DBVarsDep):
    engine = create_engine(db_vars.get_database_url(), echo=True)
    return engine


EngineDep = Annotated[Engine, Depends(get_engine)]
