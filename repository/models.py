from decimal import Decimal
from typing import Annotated

from fastapi import Depends
from sqlmodel import (
    Date,
    DateTime,
    Field,
    Relationship,
    Session,
    SQLModel,
    UniqueConstraint,
    create_engine,
    func,
)

from config.vars import EnvVars
from repository.enums import SplitType, TaskStatus

# https://stackoverflow.com/questions/224462/storing-money-in-a-decimal-column-what-precision-and-scale
MONEY_DIGITS = 13
MONEY_DECIMALS = 4


class Currency(SQLModel, table=True):
    code: str = Field(primary_key=True, min_length=3, max_length=3)
    country: str = Field(nullable=False, min_length=1)
    currency_name: str = Field(nullable=False, min_length=1)


class Account(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    balance: Decimal = Field(
        default=0.0,
        nullable=False,
        max_digits=MONEY_DIGITS,
        decimal_places=MONEY_DECIMALS,
    )
    group_id: int = Field(foreign_key="group.id", nullable=False)
    user_id: int = Field(foreign_key="user.id", nullable=False)

    created_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),  # pylint: disable=E1102
        },
    )

    updated_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),  # pylint: disable=E1102
        },
    )

    # https://github.com/fastapi/sqlmodel/issues/114
    __table_args__ = (
        UniqueConstraint(
            "group_id",
            "user_id",
            name="unique_user_account_per_group",
        ),
    )


class Expense(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    payee_id: int = Field(foreign_key="user.id", nullable=False)
    group_id: int = Field(foreign_key="group.id", nullable=False)
    group: "Group" = Relationship(back_populates="expenses")
    amount: Decimal = Field(
        ge=0.0,
        nullable=False,
        max_digits=MONEY_DIGITS,
        decimal_places=MONEY_DECIMALS,
    )
    split_type: SplitType = Field(nullable=False)
    splits: list["Split"] = Relationship(back_populates="expense")
    images: list["ExpenseImage"] = Relationship(back_populates="expense")

    created_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),  # pylint: disable=E1102
        },
    )

    updated_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),  # pylint: disable=E1102
        },
    )


class ExpenseImage(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    expense_id: int = Field(foreign_key="expense.id", nullable=False, index=True)
    expense: Expense = Relationship(back_populates="images")
    uploaded_by: int = Field(foreign_key="user.id", nullable=False)
    permalink: str = Field(min_length=1)


class Split(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    expense_id: int = Field(foreign_key="expense.id", nullable=False, index=True)
    expense: Expense = Relationship(back_populates="splits")
    amount: Decimal = Field(
        ge=0.0,
        nullable=False,
        max_digits=MONEY_DIGITS,
        decimal_places=MONEY_DECIMALS,
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "expense_id",
            name="unique_user_split_per_expense",
        ),
    )


class Task(SQLModel, table=True):
    """
    Reference: https://github.com/fastapi/sqlmodel/discussions/1038
    """

    id: int | None = Field(default=None, primary_key=True)
    status: TaskStatus = Field(default=TaskStatus.PENDING, nullable=False)
    title: str = Field(nullable=False)
    description: str | None = Field(default=None, nullable=True)

    assignee_id: int = Field(foreign_key="user.id", nullable=False)
    assignee: "User" = Relationship(
        back_populates="received_tasks",
        sa_relationship_kwargs={
            "foreign_keys": "Task.assignee_id",
        },
    )

    assigner_id: int = Field(foreign_key="user.id", nullable=False)
    assigner: "User" = Relationship(
        back_populates="assigned_tasks",
        sa_relationship_kwargs={
            "foreign_keys": "Task.assigner_id",
        },
    )

    deadline: DateTime | None = Field(default=None, nullable=True)

    created_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),  # pylint: disable=E1102
        },
    )

    updated_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),  # pylint: disable=E1102
        },
    )


class UserGroupLink(SQLModel, table=True):
    user_id: int = Field(foreign_key="user.id", primary_key=True)
    group_id: int = Field(foreign_key="group.id", primary_key=True)


class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, nullable=False)
    hashed_password: str = Field(nullable=False)
    full_name: str = Field(nullable=False)
    date_of_birth: Date | None = Field(
        default=None,
        nullable=True,
        sa_type=Date(),
    )
    mobile_number: str | None = Field(default=None, nullable=True)
    is_active: bool = Field(default=True, nullable=False)

    created_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),  # pylint: disable=E1102
        },
    )

    updated_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "onupdate": func.now(),  # pylint: disable=E1102
        },
    )

    groups: list["Group"] = Relationship(back_populates="users", link_model=UserGroupLink)

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


class Group(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, nullable=False)
    description: str | None = Field(default=None)
    display_image: str | None = Field(
        default=None,
        nullable=True,
        description="image or icon to be shown as group display image",
    )
    creator_id: int = Field(
        foreign_key="user.id",
        nullable=False,
        description="user who created the group",
    )
    admin_id: int = Field(
        foreign_key="user.id",
        nullable=False,
        description="user responsible for managing the group",
    )
    can_users_invite: bool = Field(
        default=False,
        nullable=False,
        description="whether non admin users can add other users in the group or not",
    )
    can_users_edit_info: bool = Field(
        default=False,
        nullable=False,
        description="whether non admin users can edit title and description of the group",
    )
    is_active: bool = Field(
        default=True,
        nullable=False,
        description="whether the group is currently active, expenses cannot be added to inactive groups",
    )

    currency_code: str = Field(foreign_key="currency.code", nullable=False)
    users: list["User"] = Relationship(back_populates="groups", link_model=UserGroupLink)
    expenses: list["Expense"] = Relationship(back_populates="group")

    created_at: DateTime | None = Field(
        default=None,
        sa_type=DateTime(timezone=True),
        sa_column_kwargs={
            "server_default": func.now(),  # pylint: disable=E1102
        },
    )


engine = create_engine(EnvVars().get_database_url(), echo=True)


def create_db_and_tables():
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]
