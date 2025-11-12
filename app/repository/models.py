from datetime import date, datetime
from typing import Annotated, Any

from fastapi import Depends
from fastapi.encoders import jsonable_encoder
from pydantic import EmailStr, HttpUrl, model_validator
from pydantic_extra_types.currency_code import Currency
from sqlalchemy import Engine, false
from sqlalchemy.sql.sqltypes import Date, DateTime
from sqlmodel import AutoString, Field, Relationship, SQLModel, create_engine  # type: ignore

from app.config.vars import DBVarsDep
from app.repository.base_models import CreatedAt, Enabled, Id, UpdatedAt
from app.repository.enums import MembershipStatus, SplitType, TaskStatus
from app.repository.types import TypeId, TypeMobile, TypeMoney


class Account(Id, CreatedAt, UpdatedAt, Enabled, table=True):
    user_id: TypeId = Field(foreign_key="user.id", index=True)
    group_id: TypeId = Field(foreign_key="group.id", index=True)
    balance: TypeMoney = Field(default=0.0)
    membership_status: MembershipStatus = MembershipStatus.REQUESTED
    user: "User" = Relationship(back_populates="accounts")
    group: "Group" = Relationship(back_populates="accounts")


class User(Id, CreatedAt, UpdatedAt, Enabled, table=True):
    name: str | None = Field(default=None, max_length=72, nullable=True)
    email: EmailStr | None = Field(unique=True, index=True, default=None, max_length=255, nullable=True)
    mobile: TypeMobile | None = Field(unique=True, index=True, default=None, max_length=30, nullable=True)
    password_hash: str
    dob: date | None = Field(sa_type=Date(), default=None, nullable=True)
    accounts: list[Account] = Relationship(back_populates="user")
    display_image: HttpUrl | None = Field(sa_type=AutoString, default=None, nullable=True)
    gender: str | None = Field(default=None, max_length=16, nullable=True)

    assigned_tasks: list["Task"] = Relationship(
        back_populates="assigner",
        sa_relationship_kwargs={"foreign_keys": "Task.assigner_id"},
    )

    received_tasks: list["Task"] = Relationship(
        back_populates="assignee",
        sa_relationship_kwargs={"foreign_keys": "Task.assignee_id"},
    )

    @model_validator(mode="before")
    @classmethod
    def print_out_user_data(cls, data: Any):  # type: ignore
        print("user validator before", jsonable_encoder(data))
        return data  # type: ignore

    @model_validator(mode="after")
    def _has_username(self):
        print("inside has username", jsonable_encoder(self))
        if self.email is None and self.mobile is None:
            raise ValueError("both email and mobile number cannot be missing")
        return self

    def is_active_member_of(self, group_id: TypeId) -> bool:
        return any(group_id == a.group_id for a in self.accounts if a.membership_status == MembershipStatus.ACTIVE)


class Group(Id, CreatedAt, Enabled, table=True):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, nullable=True)
    currency: Currency
    # using annotated with field and sa_type doesn't link HttpUrl to AutoString
    # type in database, so we need to assign Field here, this is special case
    display_image: HttpUrl | None = Field(sa_type=AutoString, default=None, nullable=True)
    creator_id: TypeId = Field(foreign_key="user.id")
    admin_id: TypeId = Field(foreign_key="user.id")
    can_users_invite: bool = Field(default=False, sa_column_kwargs={"server_default": false()})
    can_users_edit_info: bool = Field(default=False, sa_column_kwargs={"server_default": false()})
    accounts: list[Account] = Relationship(back_populates="group")
    expenses: list["Expense"] = Relationship(back_populates="group")

    # def is_active_member(self, user_id: TypeId) -> bool:
    #     return any(user_id == a.user_id for a in self.accounts if a.membership_status == MembershipStatus.ACTIVE)


class Task(Id, CreatedAt, UpdatedAt, table=True):
    title: str = Field(max_length=255)
    description: str | None = Field(default=None, nullable=True)
    status: TaskStatus = TaskStatus.PENDING
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


class Expense(Id, CreatedAt, UpdatedAt, table=True):
    title: str = Field(max_length=255)
    details: str | None = Field(default=None, nullable=True)
    paid_on: date = Field(sa_type=Date())
    payee_id: TypeId = Field(foreign_key="user.id")
    group_id: TypeId = Field(foreign_key="group.id")
    group: Group = Relationship(back_populates="expenses")
    amount: TypeMoney
    split_type: SplitType = SplitType.EQUAL
    splits: list["Split"] = Relationship(back_populates="expense")
    images: list["ExpenseImage"] = Relationship(back_populates="expense")


class ExpenseImage(Id, table=True):
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
