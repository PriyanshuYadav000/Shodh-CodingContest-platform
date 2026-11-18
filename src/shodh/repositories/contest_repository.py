from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shodh.models.contest import Contest, ContestStatus
from shodh.models.membership import MembershipRole


def create_contest(db: Session, contest: Contest) -> Contest:
    db.add(contest)
    db.flush()
    return contest


def get_contest_by_id(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    for_update: bool = False,
    read_lock: bool = False,
) -> Contest | None:
    statement = select(Contest).where(
        Contest.id == contest_id,
        Contest.organization_id == organization_id,
    )

    if for_update:
        statement = statement.with_for_update()
    elif read_lock:
        # PostgreSQL FOR SHARE: concurrent readers can register while a
        # cancellation/update requiring FOR UPDATE waits for these transactions.
        statement = statement.with_for_update(read=True)

    return db.scalar(statement)


def list_contests(
    db: Session,
    organization_id: UUID,
    role: MembershipRole,
    limit: int,
    offset: int,
):
    statement = select(Contest).where(
        Contest.organization_id == organization_id
    )

    # Participants must not see draft or cancelled contests.
    if role == MembershipRole.PARTICIPANT:
        statement = statement.where(
            Contest.status == ContestStatus.PUBLISHED
        )

    count_statement = (
        select(func.count())
        .select_from(statement.order_by(None).subquery())
    )
    total = db.scalar(count_statement) or 0

    statement = (
        statement.order_by(
            Contest.created_at.desc(),
            Contest.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    )
    items = db.scalars(statement).all()

    return items, total
