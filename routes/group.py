from fastapi import APIRouter
from pydantic import BaseModel

group_router = APIRouter()


class GroupCreate(BaseModel):
    name: str
    description: str | None = None


# @group_router.post('/create')
