from typing import Annotated

from fastapi import APIRouter, Body, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import EmailStr, SecretStr, StringConstraints, model_validator
from sqlmodel import and_, col, select

from app.errors.user import CodeUserExists, ErrUserExists
from app.repository.models import User
from app.repository.session import SessionDep
from app.repository.types import TypeId, TypeMobile
from app.routes.base_payload import BasePayload
from app.utils.authentication import store_user

user_router = APIRouter()


class UserRegister(BasePayload):
    name: str | None = None
    email: EmailStr | None = None
    mobile: TypeMobile | None = None
    password: Annotated[SecretStr, StringConstraints(min_length=8)]

    @model_validator(mode="after")
    def _has_username(self):
        if self.email is None and self.mobile is None:
            raise ValueError("both email and mobile number cannot be missing")
        return self


class UserIdentifier(BasePayload):
    id: TypeId


@user_router.get("/error-user-exists")
def user_exists_error():
    raise ErrUserExists(code=CodeUserExists.EMAIL_EXISTS)


@user_router.post(
    "/register",
    response_class=JSONResponse,
    response_model=UserIdentifier,
    tags=["user"],
)
def register_user(user_reg: Annotated[UserRegister, Body()], session: SessionDep):
    email_clause = and_(col(User.email).is_not(None), col(User.email) == user_reg.email)
    email_users = session.exec(select(User).where(email_clause)).all()
    if len(email_users) > 0:
        raise ErrUserExists(code=CodeUserExists.EMAIL_EXISTS)

    mobile_clause = and_(col(User.mobile).is_not(None), col(User.mobile) == user_reg.mobile)
    mobile_users = session.exec(select(User).where(mobile_clause)).all()
    if len(mobile_users) > 0:
        raise ErrUserExists(code=CodeUserExists.MOBILE_EXISTS)

    db_user = store_user(
        session,
        name=user_reg.name,
        email=user_reg.email,
        mobile=user_reg.mobile,
        password=user_reg.password.get_secret_value(),
    )
    payload = UserIdentifier(id=db_user.id)
    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(payload))
