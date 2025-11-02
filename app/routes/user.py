from typing import Annotated

from fastapi import APIRouter, status, Body
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pwdlib import PasswordHash

from app.repository.models import User
from app.routes.base_payload import BasePayload
from app.routes.currency import SessionDep

user_router = APIRouter()


class UserRegister(BasePayload):
    email: str
    full_name: str
    password: str
    mobile_number: str | None = None


class UserIdentifier(BasePayload):
    id: int
    email: str


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
    session.add(db_user)
    session.commit()
    payload = UserIdentifier(id=db_user.id, email=db_user.email)
    return JSONResponse(content=jsonable_encoder(payload), status_code=status.HTTP_201_CREATED)
