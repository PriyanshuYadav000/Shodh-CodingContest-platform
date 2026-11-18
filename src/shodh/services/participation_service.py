from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shodh.models.contest import Contest, ContestStatus
from shodh.models.participation import Participation
from shodh.repositories.contest_repository import get_contest_by_id
from shodh.repositories.participation_repository import (
    create_participation,
    get_participation,
    list_contest_participations,
)


def register_for_contest(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    user_id: UUID,
) -> Participation:
    # A shared row lock allows concurrent registrations while preventing a
    # concurrent cancellation from racing the registration eligibility check.
    contest: Contest | None = get_contest_by_id(
        db,
        organization_id,
        contest_id,
        read_lock=True,
    )

    if contest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found",
        )

    now = datetime.now(UTC)

    if contest.status != ContestStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contest is not accepting registrations",
        )

    if now < contest.registration_opens_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contest registration has not opened",
        )

    if now >= contest.starts_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contest registration is closed",
        )

    if get_participation(db, contest_id, user_id) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already registered for this contest",
        )

    participation = Participation(
        contest_id=contest_id,
        user_id=user_id,
    )

    try:
        create_participation(db, participation)
        db.commit()
        db.refresh(participation)
        return participation
    except IntegrityError as exc:
        # The composite database key is the final guard against concurrent
        # duplicate requests handled by separate application processes.
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You are already registered for this contest",
        ) from exc


def get_my_participation(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    user_id: UUID,
) -> Participation:
    contest = get_contest_by_id(db, organization_id, contest_id)

    if contest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found",
        )

    participation = get_participation(db, contest_id, user_id)

    if participation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered for this contest",
        )

    return participation


def get_contest_participants(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    limit: int,
    offset: int,
) -> dict:
    contest = get_contest_by_id(db, organization_id, contest_id)

    if contest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found",
        )

    items, total = list_contest_participations(
        db,
        contest_id,
        limit,
        offset,
    )

    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }
