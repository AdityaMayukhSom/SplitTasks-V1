from typing import Annotated

from fastapi import APIRouter, Body, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic_extra_types.currency_code import Currency

from app.errors.group import CodeGroupAuth, CodeGroupInvite, ErrGroupAuth, ErrGroupInvite
from app.repository.models import Group, User
from app.repository.session import SessionDep
from app.repository.types import TypeId
from app.routes.base_payload import BasePayload
from app.routes.security import CurrentUserDep

group_router = APIRouter()


class GroupCreate(BasePayload):
    name: str
    description: str | None = None
    currency: Currency


class GroupIdentifier(BasePayload):
    id: TypeId


@group_router.post("/create", response_class=JSONResponse, response_model=GroupIdentifier)
def create_group(
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
    )

    session.add(new_group)
    session.commit()
    payload = GroupIdentifier(id=new_group.id)

    return JSONResponse(content=jsonable_encoder(payload), status_code=status.HTTP_201_CREATED)


class GroupInvite(BasePayload):
    group_id: TypeId
    invitee_id: TypeId


@group_router.post("/invite", response_class=JSONResponse)
def invite_user(group_invite: Annotated[GroupInvite, Body()], current_user: CurrentUserDep, session: SessionDep):
    group = session.get(Group, group_invite.group_id)
    if group is None:
        raise ErrGroupInvite(
            code=CodeGroupInvite.GROUP_DOES_NOT_EXIST,
            detail="group with given id does not exist",
        )

    # if the user is not part of the group, he or she cannot invite
    if not group.includes_user(current_user.id):
        raise ErrGroupAuth(
            code=CodeGroupAuth.NOT_MEMBER_OF_GROUP,
            detail="user is not part of the group",
        )

    # after this point, the user is at least a member of the group

    if not group.can_users_invite and group.admin_id != current_user.id:
        raise ErrGroupAuth(
            code=CodeGroupAuth.NOT_AN_ADMIN,
            detail="only admin can invite new members",
        )

    invitee = session.get(User, group_invite.invitee_id)
    if invitee is None:
        raise ErrGroupInvite(
            code=CodeGroupInvite.INVITEE_DOES_NOT_EXIST,
            detail="requested invitee does not exist",
        )

    if group.includes_user(invitee.id):
        raise ErrGroupInvite(
            status=status.HTTP_409_CONFLICT,
            code=CodeGroupInvite.ALREADY_MEMBER,
            detail="invitee is already part of the group",
        )
