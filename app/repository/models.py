from datetime import date, datetime
from typing import Annotated

from fastapi import Depends
from pydantic import EmailStr, HttpUrl
from pydantic_extra_types.currency_code import Currency
from sqlalchemy import Engine
from sqlmodel import (
    AutoString,
    Date,
    DateTime,
    Field,  # type: ignore
    Relationship,
    SQLModel,
    create_engine,
)

from app.config.vars import DBVarsDep
from app.repository.base_models import CreatedAt, Enabled, Id, UpdatedAt, Validated
from app.repository.enums import MembershipStatus, SplitType, TaskStatus
from app.repository.types import TypeId, TypeMobile, TypeMoney


class Account(Id, CreatedAt, UpdatedAt, Enabled, SQLModel, table=True):
    user_id: TypeId = Field(foreign_key="user.id", index=True)
    group_id: TypeId = Field(foreign_key="group.id", index=True)
    balance: TypeMoney
    membership_status: MembershipStatus = Field(default=MembershipStatus.REQUESTED)
    user: "User" = Relationship(back_populates="accounts")
    group: "Group" = Relationship(back_populates="accounts")


class User(Validated, Id, CreatedAt, UpdatedAt, Enabled, SQLModel, table=True):
    name: str | None = Field(default=None)
    email: EmailStr | None = Field(unique=True, index=True, nullable=True)
    mobile: TypeMobile | None = Field(unique=True, index=True, nullable=True)
    password_hash: str
    dob: date | None = Field(default=None, nullable=True, sa_type=Date())
    accounts: list[Account] = Relationship(back_populates="user")

    assigned_tasks: list["Task"] = Relationship(
        back_populates="assigner",
        sa_relationship_kwargs={"foreign_keys": "Task.assigner_id"},
    )

    received_tasks: list["Task"] = Relationship(
        back_populates="assignee",
        sa_relationship_kwargs={"foreign_keys": "Task.assignee_id"},
    )

    def is_member(self, group_id: TypeId) -> bool:
        return any(group_id == a.group_id for a in self.accounts if a.membership_status == MembershipStatus.ACCEPTED)


class Group(Validated, Id, CreatedAt, Enabled, SQLModel, table=True):
    name: str = Field(min_length=1)
    description: str | None = Field(default=None)
    currency: Currency
    display_image: HttpUrl | None = Field(default=None, sa_type=AutoString)
    creator_id: TypeId = Field(foreign_key="user.id")
    admin_id: TypeId = Field(foreign_key="user.id")
    can_users_invite: bool = Field(default=False)
    can_users_edit_info: bool = Field(default=False)
    accounts: list[Account] = Relationship(back_populates="group")
    expenses: list["Expense"] = Relationship(back_populates="group")

    def includes_user(self, user_id: TypeId) -> bool:
        return any(user_id == a.user_id for a in self.accounts)


class Task(Id, CreatedAt, UpdatedAt, SQLModel, table=True):
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    title: str
    description: str | None = Field(default=None, nullable=True)
    deadline: datetime = Field(sa_type=DateTime(timezone=True))

    group_id: TypeId = Field(foreign_key="group.id")
    assignee_id: TypeId = Field(foreign_key="user.id")
    assigner_id: TypeId = Field(foreign_key="user.id")

    # Reference: https://github.com/fastapi/sqlmodel/discussions/1038
    assignee: "User" = Relationship(
        back_populates="received_tasks",
        sa_relationship_kwargs={"foreign_keys": "Task.assignee_id"},
    )

    assigner: "User" = Relationship(
        back_populates="assigned_tasks",
        sa_relationship_kwargs={"foreign_keys": "Task.assigner_id"},
    )


class Expense(Validated, Id, CreatedAt, UpdatedAt, SQLModel, table=True):
    payee_id: TypeId = Field(foreign_key="user.id")
    group_id: TypeId = Field(foreign_key="group.id")
    group: Group = Relationship(back_populates="expenses")
    amount: TypeMoney
    split_type: SplitType = Field(default=SplitType.EQUAL)
    splits: list["Split"] = Relationship(back_populates="expense")
    images: list["ExpenseImage"] = Relationship(back_populates="expense")


class ExpenseImage(Id, SQLModel, table=True):
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
