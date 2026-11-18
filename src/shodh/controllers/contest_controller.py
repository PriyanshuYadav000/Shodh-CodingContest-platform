from uuid import UUID

from sqlalchemy.orm import Session

from shodh.models.user import User
from shodh.models.membership import MembershipRole

from shodh.schemas.contest import (
    ContestCreateRequest,
    ContestUpdateRequest
)

from shodh.services.contest_service import (
    create_new_contest,
    get_organization_contests,
    get_contest_details,
    update_contest,
    publish_contest,
    cancel_contest
)


def create_contest_controller(
    db: Session,
    organization_id: UUID,
    payload: ContestCreateRequest,
    current_user: User
):

    return create_new_contest(
        db,
        organization_id,
        current_user.id,
        payload
    )


def list_contests_controller(
    db: Session,
    organization_id: UUID,
    role: MembershipRole,
    limit: int,
    offset: int
):

    return get_organization_contests(
        db,
        organization_id,
        role,
        limit,
        offset
    )


def get_contest_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID
):

    return get_contest_details(
        db,
        organization_id,
        contest_id
    )


def update_contest_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    payload: ContestUpdateRequest
):

    return update_contest(
        db,
        organization_id,
        contest_id,
        payload
    )


def publish_contest_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID
):

    return publish_contest(
        db,
        organization_id,
        contest_id
    )


def cancel_contest_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID
):

    return cancel_contest(
        db,
        organization_id,
        contest_id
    )