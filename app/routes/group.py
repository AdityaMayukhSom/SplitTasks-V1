from typing import Annotated

from fastapi import APIRouter, Body
from pydantic import BaseModel
from starlette.responses import JSONResponse

from app.repository.models import SessionDep, Group
from app.routes.security import CurrentUserDep

group_router = APIRouter()


class GroupCreate(BaseModel):
    name: str
    description: str | None = None
    currency_code: str


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
