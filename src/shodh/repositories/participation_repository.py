from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from shodh.models.participation import Participation


def get_participation(
    db: Session,
    contest_id: UUID,
    user_id: UUID,
) -> Participation | None:
    return db.get(Participation, (contest_id, user_id))


def create_participation(
    db: Session,
    participation: Participation,
) -> Participation:
    db.add(participation)
    db.flush()
    return participation


def list_contest_participations(
    db: Session,
    contest_id: UUID,
    limit: int,
    offset: int,
) -> tuple[list[Participation], int]:
    filters = (Participation.contest_id == contest_id,)

    total = db.scalar(
        select(func.count())
        .select_from(Participation)
        .where(*filters)
    ) or 0

    statement = (
        select(Participation)
        .options(joinedload(Participation.user))
        .where(*filters)
        .order_by(
            Participation.registered_at.asc(),
            Participation.user_id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )

    return db.scalars(statement).all(), total
