from typing import Annotated, Literal

from fastapi import APIRouter, status, Body
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pwdlib import PasswordHash
from pydantic import Field, EmailStr, SecretStr, StringConstraints
from pydantic_extra_types.phone_numbers import PhoneNumber
from sqlalchemy.exc import IntegrityError

from app.repository.base_models import TypeId
from app.repository.models import User
from app.repository.session import SessionDep
from app.routes.base_payload import BasePayload, BaseError

user_router = APIRouter()


class UserRegister(BasePayload):
    email: EmailStr
    full_name: str = Field(min_length=2)
    password: Annotated[SecretStr, StringConstraints(min_length=8)]
    mobile_number: PhoneNumber


class UserIdentifier(BasePayload):
    id: TypeId
    email: EmailStr


class UserExistsError(BaseError):
    error: Literal["email_exists", "mobile_number_exists"]


@user_router.post("/register", response_class=JSONResponse, response_model=UserIdentifier, tags=["user"])
async def register_user(user_register: Annotated[UserRegister, Body()], session: SessionDep):
    hasher = PasswordHash.recommended()
    hashed_password = hasher.hash(user_register.password.get_secret_value())

    db_user = User(
        full_name=user_register.full_name,
        email=user_register.email,
        mobile_number=user_register.mobile_number,
        hashed_password=hashed_password,
    )

    try:
        session.add(db_user)
        session.commit()
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=UserExistsError(
                error="email_exists",
                error_description="account with given email already exists",
            ).model_dump(),
        )

    payload = UserIdentifier(id=db_user.id, email=db_user.email)
    return JSONResponse(content=payload.model_dump(mode="json"), status_code=status.HTTP_201_CREATED)
