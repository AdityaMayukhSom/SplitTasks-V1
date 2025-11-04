from typing import Annotated, Literal

from fastapi import APIRouter, status, Body
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse
from pwdlib import PasswordHash
from pydantic import Field
from sqlalchemy.exc import IntegrityError

from app.repository.models import User
from app.routes.base_payload import BasePayload
from app.routes.currency import SessionDep

user_router = APIRouter()


class UserRegister(BasePayload):
    email: str
    full_name: str
    password: str = Field(min_length=8)
    mobile_number: str | None = None


class UserIdentifier(BasePayload):
    id: int
    email: str


class UserExistsError(BasePayload):
    error: Literal["duplicate_email"]
    error_description: str


@user_router.post("/register", response_class=JSONResponse, response_model=UserIdentifier, tags=["user"])
async def register_user(user_register: Annotated[UserRegister, Body()], session: SessionDep):
    hasher = PasswordHash.recommended()
    hashed_password = hasher.hash(user_register.password)

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
        err_data = UserExistsError(
            error="duplicate_email",
            error_description="account with given email already exists",
        )

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=err_data.model_dump(),
        )

    payload = UserIdentifier(id=db_user.id, email=db_user.email)
    return JSONResponse(content=payload.model_dump(), status_code=status.HTTP_201_CREATED)
