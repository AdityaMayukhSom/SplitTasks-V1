from argon2 import PasswordHasher
from fastapi import APIRouter
from pydantic import BaseModel, Field

from repository.models import User
from routes.currency import SessionDep

user_router = APIRouter()


class UserRegister(BaseModel):
    email: str
    full_name: str = Field(alias="fullName")
    password: str
    mobile_number: str | None = None


@user_router.post("/register", response_model=int)
async def register_user(user_register: UserRegister, session: SessionDep):
    ph = PasswordHasher()
    hashed_password = ph.hash(user_register.password)
    db_user = User.model_validate(
        user_register,
        update={
            "hashed_password": hashed_password,
        },
    )
    session.add(db_user)
    session.commit()
    return db_user.id
