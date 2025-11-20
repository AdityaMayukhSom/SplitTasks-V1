import math
from datetime import date
from typing import Annotated

from fastapi import APIRouter, Body, status

from app.errors.error import CodeItemNotFound, ErrItemNotFound
from app.repository.enums import MembershipStatus
from app.repository.models import Account, Expense, Group, Split
from app.repository.session import SessionDep
from app.repository.types import TypeId, TypeMoney, id_to_str
from app.routes.base_payload import BasePayload
from app.routes.security import CurrentUserDep


class SplitPayload(BasePayload):
    user_id: TypeId
    amount: TypeMoney


class ExpensePayload(BasePayload):
    title: str
    paid_by: TypeId
    group_id: TypeId
    details: str | None = None
    paid_on: date
    amount: TypeMoney
    splits: list[SplitPayload]


expense_router = APIRouter(tags=["expenses"])


def validate_active_group_members_have_split_entry(group: Group, payload: ExpensePayload):
    group_users = [id_to_str(a.owner_id) for a in group.accounts if a.membership_status == MembershipStatus.ACTIVE]
    if len(group_users) != len(set(group_users)):
        # same user with active status exists multiple time in DB
        raise

    payload_users = [id_to_str(split.user_id) for split in payload.splits]
    if len(payload_users) != len(set(payload_users)):
        # duplicate entries for one user exist
        raise

    if set(group_users) != set(payload_users):
        # users in payload does not belong to the group
        raise


def validate_expense_amount_matches_split_total(payload: ExpensePayload):
    split_sum = sum(s.amount for s in payload.splits)
    if not math.isclose(payload.amount, split_sum, rel_tol=1e-4):
        # sum of split is not equal to the total amount
        raise


def validate_expense_can_be_added_for_account(account: Account, group: Group):
    if not account.enabled:
        raise

    if not account.owner.is_active_member_of(group.id):
        raise


# ─────────────────────────────────────────────────────────────
# CREATE EXPENSE
# ─────────────────────────────────────────────────────────────


@expense_router.post("", status_code=status.HTTP_201_CREATED)
def create_expense(
    payload: Annotated[ExpensePayload, Body()],
    current_user: CurrentUserDep,
    session: SessionDep,
):
    group = session.get(Group, payload.group_id)
    if group is None:
        raise ErrItemNotFound(code=CodeItemNotFound.GROUP_NOT_FOUND)

    if not current_user.is_active_member_of(group.id):
        # only a member of a group can add expense in the group
        raise

    validate_active_group_members_have_split_entry(group, payload)
    validate_expense_amount_matches_split_total(payload)

    ac_map = {id_to_str(ac.id): ac for ac in group.accounts}

    # add the balance to the user who actually paid
    paid_by_ac = ac_map.get(id_to_str(payload.paid_by))
    if paid_by_ac is None:
        raise

    validate_expense_can_be_added_for_account(paid_by_ac, group)

    paid_by_ac.balance += payload.amount
    session.add(paid_by_ac)

    expense = Expense(
        title=payload.title,
        details=payload.details,
        group_id=payload.group_id,
        group=group,
        paid_by=payload.paid_by,
        created_by=current_user.id,
        amount=payload.amount,
        paid_on=payload.paid_on,
        splits=[],
        images=[],
    )

    for ps in payload.splits:
        # create a split to show in the group
        s = Split(user_id=ps.user_id, amount=ps.amount)
        expense.splits.append(s)

        # update the balance for this account
        ac = ac_map.get(id_to_str(ps.user_id))
        if ac is None:
            # this is impossible condition as previously we have checked all users in the group
            # are in the expense and this map contains mapping for all users in the group. this
            # is to satisfy pylance because it thinks map might not have the key
            raise
        ac.balance -= ps.amount

        session.add(s)
        session.add(ac)

    session.add(expense)
    session.commit()
    session.refresh(expense)

    return expense


# ─────────────────────────────────────────────────────────────
# UPDATE EXPENSE
# ─────────────────────────────────────────────────────────────


@expense_router.put("/{expense_id}")
def update_expense(
    expense_id: TypeId,
    payload: Annotated[ExpensePayload, Body()],
    current_user: CurrentUserDep,
    session: SessionDep,
):
    expense = session.get(Expense, expense_id)
    if not expense:
        raise

    if expense.group_id != payload.group_id:
        # ensure the expense id belongs to the same group
        raise

    if not current_user.is_active_member_of(expense.group_id):
        # only if
        raise

    validate_active_group_members_have_split_entry(expense.group, payload)
    validate_expense_amount_matches_split_total(payload)

    expense.title = payload.title
    expense.details = payload.details
    expense.paid_on = payload.paid_on

    # revert back old split amounts and add new split amounts

    ac_map = {id_to_str(ac.id): ac for ac in expense.group.accounts}
    split_map = {id_to_str(split.user_id): split for split in expense.splits}

    # add the balance to the user who actually paid
    new_paid_by_ac = ac_map.get(id_to_str(payload.paid_by))
    old_paid_by_ac = ac_map.get(id_to_str(expense.paid_by))

    if old_paid_by_ac is None:
        # this branch should never be triggered as old account should exist
        # Question - balances for an inactive account can still be updated but not added?
        # But what is someone has left the group and their balance is settled and then
        # someone tries to update the balance and makes his account balance positive?
        # Possible Solution - check whether paid_by account is active atleast.
        raise

    if new_paid_by_ac is None:
        # ensure the account who paid exists in the group
        raise

    validate_expense_can_be_added_for_account(new_paid_by_ac, expense.group)
    validate_expense_can_be_added_for_account(old_paid_by_ac, expense.group)

    old_paid_by_ac.balance -= expense.amount
    new_paid_by_ac.balance += payload.amount

    expense.amount = payload.amount
    expense.paid_by = payload.paid_by

    session.add(old_paid_by_ac)
    session.add(new_paid_by_ac)

    for ps in payload.splits:
        # create a split to show in the group
        s = split_map.get(id_to_str(ps.user_id))
        assert s is not None

        # update the balance for this account
        ac = ac_map.get(id_to_str(ps.user_id))
        assert ac is not None

        ac.balance += s.amount
        ac.balance -= ps.amount
        s.amount = ps.amount

        session.add(s)
        session.add(ac)

    session.add(expense)
    session.commit()
    session.refresh(expense)

    return expense


# ─────────────────────────────────────────────────────────────
# ADD IMAGE
# ─────────────────────────────────────────────────────────────

# @expense_router.post("/{expense_id}/images")
# def add_expense_image(
#     expense_id: str,
#     permalink: str = Body(...),
#     current_user: CurrentUserDep,
#     session: SessionDep,
# ):
#     expense = session.exec(select(Expense).where(Expense.id == expense_id)).one_or_none()
#     if not expense:
#         raise HTTPException(404, "Expense not found")

#     ensure_user_in_group(current_user, expense.group_id)

#     image = ExpenseImage(
#         uploaded_by=current_user.id,
#         expense_id=expense_id,
#         permalink=permalink,
#     )

#     session.add(image)
#     session.commit()
#     return image


# ─────────────────────────────────────────────────────────────
# DELETE
# ─────────────────────────────────────────────────────────────


@expense_router.delete("/{expense_id}", status_code=204)
def delete_expense(
    expense_id: TypeId,
    current_user: CurrentUserDep,
    session: SessionDep,
):
    expense = session.get(Expense, expense_id)
    if not expense:
        # no expense with given id exists
        raise

    if not current_user.is_active_member_of(expense.group_id):
        # only current members of the group can delete expense
        raise

    if not expense.group.can_users_delete_expense and current_user.id != expense.group.admin_id:
        raise

    session.delete(expense)
    session.commit()
