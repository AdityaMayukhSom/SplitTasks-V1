from typing import Annotated, Literal

from fastapi import APIRouter, Body, HTTPException, status
from fastapi.encoders import jsonable_encoder
from pydantic_extra_types.currency_code import Currency
from starlette.responses import JSONResponse

from app.repository.models import Group, User
from app.repository.session import SessionDep
from app.repository.types import TypeId
from app.routes.base_payload import BaseError, BasePayload
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


class GroupAuthorizationError(
    BaseError[
        Literal[
            "not_member_of_group",
            "not_an_admin",
        ]
    ]
):
    pass


class GroupInvitationError(
    BaseError[
        Literal[
            "already_member",
            "invitee_does_not_exist",
            "group_does_not_exist",
            "already_pending_request",
            "unable_to_invite",
        ]
    ]
):
    pass


@group_router.post("/invite", response_class=JSONResponse)
def invite_user(group_invite: Annotated[GroupInvite, Body()], current_user: CurrentUserDep, session: SessionDep):
    group = session.get(Group, group_invite.group_id)
    if group is None:
        err_pl = GroupInvitationError(
            error="group_does_not_exist", error_description="group with given id does not exist"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_pl.model_dump())

    # if the user is not part of the group, he or she cannot invite
    if not group.includes_user(current_user.id):
        err_pl = GroupAuthorizationError(
            error="not_member_of_group",
            error_description="user is not part of the group",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err_pl.model_dump())

    # after this point, the user is at least a member of the group

    if not group.can_users_invite and group.admin_id != current_user.id:
        err_pl = GroupAuthorizationError(
            error="not_an_admin",
            error_description="only admin can invite new members",
        )
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=err_pl.model_dump())

    invitee = session.get(User, group_invite.invitee_id)
    if invitee is None:
        err_pl = GroupInvitationError(
            error="invitee_does_not_exist", error_description="requested invitee does not exist"
        )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=err_pl.model_dump())

    if group.includes_user(invitee.id):
        err_pl = GroupInvitationError(
            error="already_member",
            error_description="invitee is already part of the group",
        )
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=err_pl.model_dump())
