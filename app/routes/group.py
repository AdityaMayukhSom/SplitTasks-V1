from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel
from pydantic_extra_types.currency_code import Currency
from starlette.responses import JSONResponse

from app.repository.models import Group
from app.repository.session import SessionDep
from app.routes.security import CurrentUserDep

group_router = APIRouter()


class GroupCreate(BaseModel):
    name: str
    description: str | None = None
    currency_code: Currency


@group_router.post("/create", response_class=JSONResponse)
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
        currency_code=group_create.currency_code,
    )
