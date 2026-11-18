from uuid import UUID

from sqlalchemy.orm import Session

from shodh.services.participation_service import (
    get_contest_participants,
    get_my_participation,
    register_for_contest,
)


def register_for_contest_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    user_id: UUID,
):
    return register_for_contest(
        db,
        organization_id,
        contest_id,
        user_id,
    )


def get_my_participation_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    user_id: UUID,
):
    return get_my_participation(
        db,
        organization_id,
        contest_id,
        user_id,
    )


def list_contest_participants_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    limit: int,
    offset: int,
):
    return get_contest_participants(
        db,
        organization_id,
        contest_id,
        limit,
        offset,
    )
