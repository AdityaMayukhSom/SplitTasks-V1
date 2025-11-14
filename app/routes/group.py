from datetime import datetime, timezone
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Body, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic_extra_types.currency_code import Currency

from app.errors.error import (
    CodeGroupAuth,
    CodeGroupInvite,
    CodeInvitationAuth,
    CodeItemNotFound,
    ErrGroupAuth,
    ErrGroupInvite,
    ErrInvitationAuth,
    ErrItemNotFound,
)
from app.repository.models import Account, Group, User
from app.repository.session import SessionDep
from app.repository.types import TypeId, id_to_str
from app.routes.base_payload import BasePayload
from app.routes.security import CurrentUserDep

group_router = APIRouter()


class GroupCreate(BasePayload):
    name: str
    description: str | None = None
    currency: Currency


class GroupIdentifier(BasePayload):
    id: TypeId


@group_router.post(
    "/create",
    response_class=JSONResponse,
    response_model=GroupIdentifier,
    status_code=status.HTTP_201_CREATED,
    tags=["group"],
)
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

    return JSONResponse(status_code=status.HTTP_201_CREATED, content=jsonable_encoder(payload))


class InviteUser(BasePayload):
    group_id: TypeId
    invitee_id: TypeId


class GroupInvitation(BasePayload):
    account_id: TypeId
    group_id: TypeId
    invitee_id: TypeId
    invitee_name: str | None
    inviter_id: TypeId
    requested_at: datetime


@group_router.post("/invite", response_class=JSONResponse, response_model=GroupInvitation, tags=["group", "account"])
def invite_user(invitation: Annotated[InviteUser, Body()], current_user: CurrentUserDep, session: SessionDep):
    group = session.get(Group, invitation.group_id)

    if group is None:
        group_id_str = id_to_str(invitation.invitee_id)
        raise ErrItemNotFound(
            code=CodeItemNotFound.GROUP_NOT_FOUND,
            detail=f"group with id ${group_id_str} not found",
        )

    # if the user is not part of the group, he or she cannot invite
    if not current_user.is_active_member_of(group.id):
        raise ErrGroupAuth(
            code=CodeGroupAuth.FORBIDDEN_NOT_MEMBER,
            detail="user trying to invite is not part of the group",
        )

    # after this point, the user is at least a member of the group

    if not group.can_users_invite and group.admin_id != current_user.id:
        raise ErrInvitationAuth(
            code=CodeInvitationAuth.ADMIN_ONLY_ACCESS,
            detail="only admin can invite new members",
        )

    invitee = session.get(User, invitation.invitee_id)
    if invitee is None:
        invitee_id_str = id_to_str(invitation.invitee_id)
        raise ErrItemNotFound(
            code=CodeItemNotFound.USER_NOT_FOUND,
            detail=f"no user with id ${invitee_id_str} found.",
        )

    if invitee.is_active_member_of(group.id):
        raise ErrGroupInvite(
            status=status.HTTP_409_CONFLICT,
            code=CodeGroupInvite.INVITEE_ALREADY_MEMBER,
            detail="invitee is already part of the group",
        )

    account = Account(
        owner_id=invitee.id,
        group_id=group.id,
        invited_by=current_user.id,
        balance=Decimal(0.0),
        invited_at=datetime.now(timezone.utc),
    )
    session.add(account)
    session.commit()
    payload = GroupInvitation(
        account_id=account.id,
        group_id=group.id,
        invitee_id=invitee.id,
        invitee_name=invitee.name,
        inviter_id=current_user.id,
        requested_at=account.invited_at,
    )
    return JSONResponse(content=jsonable_encoder(payload))
