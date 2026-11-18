from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shodh.models.contest import Contest, ContestStatus
from shodh.models.membership import MembershipRole
from shodh.repositories.contest_repository import (
    create_contest,
    get_contest_by_id,
    list_contests,
)
from shodh.schemas.contest import ContestCreateRequest, ContestUpdateRequest


def validate_schedule(
    registration_opens_at: datetime,
    starts_at: datetime,
    ends_at: datetime,
) -> None:
    if not registration_opens_at < starts_at < ends_at:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid contest schedule",
        )


def create_new_contest(
    db: Session,
    organization_id: UUID,
    creator_id: UUID,
    payload: ContestCreateRequest,
) -> Contest:
    contest = Contest(
        organization_id=organization_id,
        created_by=creator_id,
        title=payload.title,
        slug=payload.slug,
        description=payload.description,
        registration_opens_at=payload.registration_opens_at,
        starts_at=payload.starts_at,
        ends_at=payload.ends_at,
        wrong_attempt_penalty_minutes=payload.wrong_attempt_penalty_minutes,
        status=ContestStatus.DRAFT,
    )

    try:
        create_contest(db, contest)
        db.commit()
        db.refresh(contest)
        return contest
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contest slug already exists in this organization",
        ) from exc


def get_organization_contests(
    db: Session,
    organization_id: UUID,
    role: MembershipRole,
    limit: int,
    offset: int,
) -> dict:
    items, total = list_contests(
        db,
        organization_id,
        role,
        limit,
        offset,
    )
    return {
        "items": items,
        "total": total,
        "limit": limit,
        "offset": offset,
    }


def get_contest_details(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    role: MembershipRole,
) -> Contest:
    contest = get_contest_by_id(db, organization_id, contest_id)

    # Keep draft and cancelled contest details private from participants,
    # matching the filtering applied by the contest-list endpoint.
    if contest is None or (
        role == MembershipRole.PARTICIPANT
        and contest.status != ContestStatus.PUBLISHED
    ):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found",
        )

    return contest


def update_contest(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    payload: ContestUpdateRequest,
) -> Contest:
    contest = get_contest_by_id(
        db,
        organization_id,
        contest_id,
        for_update=True,
    )

    if contest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found",
        )

    if contest.status != ContestStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft contests can be updated",
        )

    changes = payload.model_dump(exclude_unset=True)
    for field, value in changes.items():
        if field != "description" and value is None:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"{field} cannot be null",
            )

    validate_schedule(
        changes.get("registration_opens_at", contest.registration_opens_at),
        changes.get("starts_at", contest.starts_at),
        changes.get("ends_at", contest.ends_at),
    )

    for field, value in changes.items():
        setattr(contest, field, value)

    try:
        db.commit()
        db.refresh(contest)
        return contest
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contest slug already exists",
        ) from exc


def publish_contest(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
) -> Contest:
    contest = get_contest_by_id(
        db,
        organization_id,
        contest_id,
        for_update=True,
    )

    if contest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found",
        )

    if contest.status != ContestStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Only draft contests can be published",
        )

    if datetime.now(UTC) >= contest.starts_at:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot publish a contest after it has started",
        )

    contest.status = ContestStatus.PUBLISHED
    db.commit()
    db.refresh(contest)
    return contest


def cancel_contest(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
) -> Contest:
    contest = get_contest_by_id(
        db,
        organization_id,
        contest_id,
        for_update=True,
    )

    if contest is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Contest not found",
        )

    if contest.status == ContestStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Contest is already cancelled",
        )

    contest.status = ContestStatus.CANCELLED
    db.commit()
    db.refresh(contest)
    return contest
