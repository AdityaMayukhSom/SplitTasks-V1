from collections.abc import Sequence
from datetime import datetime, timezone

from fastapi import APIRouter
from sqlmodel import col, select, update

from app.errors.error import (
    CodeAccountAuth,
    CodeGroupAuth,
    CodeInvitation,
    CodeInvitationAuth,
    CodeItemNotFound,
    ErrAccountAuth,
    ErrGroupAuth,
    ErrInvitation,
    ErrInvitationAuth,
    ErrItemNotFound,
)
from app.repository.enums import MembershipStatus
from app.repository.models import Account, Group
from app.repository.session import SessionDep
from app.repository.types import TypeId
from app.routes.security import CurrentUserDep

invitation_router = APIRouter()


class ErrMsgInvitation:
    NOT_OWNER = "unauthorised; invitation does not belong to user"
    DID_NOT_INVITE = "unauthorised; invitation was not created by current user"
    ACCOUNT_DISABLED = "account disabled; invitation cannot be processed"
    ALREADY_CANCELLED = "invitation is cancelled; contact admin or create a new invitation"
    ALREADY_DECLINED = "invitation has been declined; contact admin or create a new invitation"
    ALREADY_ACTIVE = "invitation has been accepted"
    NOT_PENDING = "invitation not pending anymore; contact admin or create another invitation"


@invitation_router.get("/pending/user", response_model=Sequence[Account], tags=["invitation", "user"])
def get_pending_user_invitations(current_user: CurrentUserDep, session: SessionDep):
    stmt = (
        select(Account)
        .where(
            col(Account.owner_id) == current_user.id,
            col(Account.membership_status) == MembershipStatus.PENDING,
        )
        .order_by(col(Account.invited_at))
    )
    accounts = session.exec(stmt).all()
    return accounts


@invitation_router.get("/pending/group/{group_id}", response_model=list[Account], tags=["invitation", "group"])
def get_pending_group_invitations(group_id: TypeId, current_user: CurrentUserDep, session: SessionDep):
    group = session.get(Group, group_id)
    if group is None:
        raise ErrItemNotFound(code=CodeItemNotFound.GROUP_NOT_FOUND)
    if not current_user.is_active_member_of(group.id):
        raise ErrGroupAuth(code=CodeGroupAuth.FORBIDDEN_NOT_MEMBER)
    if not group.can_users_see_invitations and group.admin_id != current_user.id:
        err_msg = "only admin can view pending invitations"
        raise ErrInvitationAuth(code=CodeInvitationAuth.ADMIN_ONLY_ACCESS, detail=err_msg)
    stmt = (
        select(Account)
        .where(
            col(Account.group_id) == group_id,
            col(Account.membership_status) == MembershipStatus.PENDING,
        )
        .order_by(col(Account.invited_at))
    )
    accounts = session.exec(stmt).all()
    return accounts


def confirm_processability(account: Account) -> None:
    if not account.enabled:
        raise ErrInvitation(code=CodeInvitation.ACCOUNT_DISABLED, detail=ErrMsgInvitation.ACCOUNT_DISABLED)

    if account.membership_status == MembershipStatus.CANCELLED:
        raise ErrInvitation(code=CodeInvitation.ALREADY_CANCELLED, detail=ErrMsgInvitation.ALREADY_CANCELLED)

    if account.membership_status == MembershipStatus.DECLINED:
        raise ErrInvitation(code=CodeInvitation.ALREADY_DECLINED, detail=ErrMsgInvitation.ALREADY_DECLINED)

    if account.membership_status == MembershipStatus.ACTIVE:
        raise ErrInvitation(code=CodeInvitation.ALREADY_ACCEPTED, detail=ErrMsgInvitation.ALREADY_ACTIVE)

    if account.membership_status != MembershipStatus.PENDING:
        # This is statement ensures that the current invitation is valid and
        # the user did not change the state of the current invitation previously
        raise ErrInvitation(code=CodeInvitation.ALREADY_PROCESSED, detail=ErrMsgInvitation.NOT_PENDING)


@invitation_router.get("/accept/{invitation_id}", tags=["invitation"])
def accept_invitation(invitation_id: TypeId, current_user: CurrentUserDep, session: SessionDep):
    account = session.get(Account, invitation_id)
    if account is None:
        raise ErrItemNotFound(code=CodeItemNotFound.INVITATION_NOT_FOUND)

    if account.owner_id != current_user.id:
        raise ErrAccountAuth(code=CodeAccountAuth.FORBIDDEN_NOT_OWNER, detail=ErrMsgInvitation.NOT_OWNER)

    confirm_processability(account)

    # only proceed if the membership status for this account is pending
    if current_user.is_active_member_of(account.group_id):
        # Q. Why is this if condition necessary if we have already checked if the membership status is pending?
        # A. We have checked if the membership status for this invitation is pending or not, but it might
        # happen that via a different account the user is member of the same group, so we will check if the
        # user is a member of the given group or not to not add a member in a group twice.

        # If inside this section, it means user is member of the group through some other account
        # In case we want to remove old stale invitations from the table, this is the place to do that
        # In future we might delete old invitations and put them into some table for audit purpose only,
        # that will keep the account table small and fast.
        mark_stmt = (
            update(Account)
            .where(
                col(Account.id) != account.id,
                col(Account.owner_id) == current_user.id,
                col(Account.group_id) == account.group_id,
                col(Account.membership_status) == MembershipStatus.PENDING,
            )
            .values(membership_status=MembershipStatus.ALTERNATE)
        )
        session.exec(mark_stmt)
        session.commit()

        err_msg = "user already member of the group"
        raise ErrInvitation(code=CodeInvitation.ALREADY_MEMBER, detail=err_msg)

    account.member_since = datetime.now(timezone.utc)
    account.membership_status = MembershipStatus.ACTIVE
    session.add(account)
    session.commit()


@invitation_router.get("/decline/{invitation_id}", tags=["invitation"])
def decline_invitation(invitation_id: TypeId, current_user: CurrentUserDep, session: SessionDep):
    account = session.get(Account, invitation_id)
    if account is None:
        raise ErrItemNotFound(code=CodeItemNotFound.INVITATION_NOT_FOUND)

    if account.owner_id != current_user.id:
        raise ErrAccountAuth(code=CodeAccountAuth.FORBIDDEN_NOT_OWNER, detail=ErrMsgInvitation.NOT_OWNER)

    confirm_processability(account)

    account.membership_status = MembershipStatus.DECLINED
    session.add(account)
    session.commit()


@invitation_router.get("/cancel/{invitation_id}", tags=["invitation"])
def cancel_invitation(invitation_id: TypeId, current_user: CurrentUserDep, session: SessionDep):
    account = session.get(Account, invitation_id)
    if account is None:
        raise ErrItemNotFound(code=CodeItemNotFound.INVITATION_NOT_FOUND)

    if account.invited_by != current_user.id:
        raise ErrAccountAuth(code=CodeAccountAuth.FORBIDDEN_DID_NOT_INVITE, detail=ErrMsgInvitation.DID_NOT_INVITE)

    confirm_processability(account)

    account.membership_status = MembershipStatus.CANCELLED
    session.add(account)
    session.commit()
