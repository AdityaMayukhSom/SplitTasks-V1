from datetime import timezone, datetime, timedelta
from typing import Annotated

import jwt
from fastapi import APIRouter, Body, status
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from pydantic_extra_types.currency_code import Currency
from starlette.responses import JSONResponse

from app.config.vars import JWTVars
from app.repository.models import Group
from app.repository.session import SessionDep
from app.repository.types import TypeId
from app.routes.security import CurrentUserDep

group_router = APIRouter()


class GroupCreate(BaseModel):
    name: str
    description: str | None = None
    currency: Currency


class GroupIdentifier(BaseModel):
    id: TypeId


def create_access_token(subject: str, jwt_vars: JWTVars) -> str:
    current_time = datetime.now(tz=timezone.utc)
    expiry_delta = timedelta(minutes=jwt_vars.expiry_minutes)
    expiry_time = current_time + expiry_delta
    payload = {
        # JWT subject has to be a string
        "sub": subject,
        "iat": current_time,
        "exp": expiry_time,
        "iss": jwt_vars.issuer,
    }
    encoded_jwt = jwt.encode(payload, jwt_vars.secret_key, algorithm=jwt_vars.signing_algo)
    return encoded_jwt


@group_router.post("/create", response_class=JSONResponse, response_model=GroupIdentifier)
async def create_group(
        group_create: Annotated[GroupCreate, Body()],
        current_user: CurrentUserDep,
        session: SessionDep,
):
    new_group = Group(
        name=group_create.name,
        description=group_create.description,
        creator_id=current_user.id,
        admin_id=current_user.id,
        currency=group_create.currency,
        users=[current_user],
    )

    session.add(new_group)
    session.commit()
    payload = GroupIdentifier(id=new_group.id)

    return JSONResponse(content=jsonable_encoder(payload), status_code=status.HTTP_201_CREATED)
