from typing import Annotated, Literal

from fastapi import APIRouter, Body, status
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pydantic import EmailStr, Field, SecretStr, StringConstraints, model_validator
from sqlmodel import and_, col, or_, select

from app.repository.models import User
from app.repository.session import SessionDep
from app.repository.types import TypeId, TypeMobile
from app.routes.base_payload import BaseError, BasePayload
from app.utils.authentication import store_user

user_router = APIRouter()


class UserRegister(BasePayload):
    name: str | None = Field(default=None)
    email: EmailStr | None = Field(default=None)
    mobile: TypeMobile | None = Field(default=None)
    password: Annotated[SecretStr, StringConstraints(min_length=8)]

    @model_validator(mode="after")
    def _has_username(self):
        email_missing = self.email is None
        mobile_missing = self.mobile is None
        if email_missing and mobile_missing:
            raise ValueError("both email and mobile number cannot be missing")
        return self


class UserIdentifier(BasePayload):
    id: TypeId


class UserExistsError(
    BaseError[
        Literal[
            "username_exists",
            "email_exists",
            "mobile_number_exists",
            "no_username_field",
        ]
    ]
):
    pass


@user_router.post("/register", response_class=JSONResponse, response_model=UserIdentifier, tags=["user"])
def register_user(user_reg: Annotated[UserRegister, Body()], session: SessionDep):
    stmt_1 = and_(col(User.email).is_not(None), col(User.email) == user_reg.email)
    stmt_2 = and_(col(User.mobile).is_not(None), col(User.mobile) == user_reg.mobile)
    user_stmt = select(User).where(or_(stmt_1, stmt_2))
    users = session.exec(user_stmt).all()

    if len(users) > 0:
        err_payload = UserExistsError(
            error="username_exists",
            error_description="existing account with given email or mobile",
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_payload.model_dump())

    db_user = store_user(
        session,
        name=user_reg.name,
        email=user_reg.email,
        mobile=user_reg.mobile,
        password=user_reg.password.get_secret_value(),
    )
    payload = UserIdentifier(id=db_user.id)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=payload.model_dump(mode="json"))
