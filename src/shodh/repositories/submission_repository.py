from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shodh.models.submission import Submission, SubmissionStatus, VerdictAttempt


def create_submission(db: Session, item: Submission) -> Submission:
    db.add(item)
    db.flush()
    return item


def get_submission(db: Session, submission_id: UUID) -> Submission | None:
    return db.get(Submission, submission_id)


def list_submissions(
    db: Session,
    contest_id: UUID,
    user_id: UUID | None,
    limit: int,
    offset: int,
):
    statement = select(Submission).where(Submission.contest_id == contest_id)
    if user_id is not None:
        statement = statement.where(Submission.user_id == user_id)

    items = db.scalars(
        statement.order_by(
            Submission.created_at.desc(),
            Submission.id.asc(),
        )
        .limit(limit)
        .offset(offset)
    ).all()
    total = db.scalar(
        select(func.count()).select_from(statement.subquery())
    ) or 0
    return items, total


def create_attempt(db: Session, item: VerdictAttempt) -> VerdictAttempt:
    db.add(item)
    db.flush()
    return item


def next_attempt_number(db: Session, submission_id: UUID) -> int:
    current = db.scalar(
        select(func.max(VerdictAttempt.attempt_number)).where(
            VerdictAttempt.submission_id == submission_id
        )
    ) or 0
    return current + 1


def list_attempts(db: Session, submission_id: UUID) -> list[VerdictAttempt]:
    return db.scalars(
        select(VerdictAttempt)
        .where(VerdictAttempt.submission_id == submission_id)
        .order_by(VerdictAttempt.attempt_number.asc())
    ).all()


def claim_next_submission(db: Session) -> Submission | None:
    """Atomically claim one queued submission for a worker process."""
    statement = (
        select(Submission)
        .where(Submission.status == SubmissionStatus.QUEUED)
        .order_by(Submission.created_at.asc(), Submission.id.asc())
        .limit(1)
        .with_for_update(skip_locked=True)
    )
    submission = db.scalar(statement)
    if submission is None:
        return None

    submission.status = SubmissionStatus.RUNNING
    submission.started_at = datetime.now(UTC)
    db.commit()
    db.refresh(submission)
    return submission
