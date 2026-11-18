from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from shodh.models.submission import Submission, VerdictAttempt


def create_submission(db: Session, item: Submission): db.add(item); db.flush(); return item
def get_submission(db: Session, submission_id: UUID): return db.get(Submission, submission_id)
def list_submissions(db: Session, contest_id: UUID, user_id: UUID | None, limit: int, offset: int):
    q=select(Submission).where(Submission.contest_id==contest_id)
    if user_id: q=q.where(Submission.user_id==user_id)
    return db.scalars(q.order_by(Submission.created_at.desc(),Submission.id.asc()).limit(limit).offset(offset)).all(), db.scalar(select(func.count()).select_from(q.subquery())) or 0
def create_attempt(db: Session, item: VerdictAttempt): db.add(item); db.flush(); return item
def next_attempt_number(db: Session, submission_id: UUID): return (db.scalar(select(func.max(VerdictAttempt.attempt_number)).where(VerdictAttempt.submission_id==submission_id)) or 0)+1
def list_attempts(db: Session, submission_id: UUID): return db.scalars(select(VerdictAttempt).where(VerdictAttempt.submission_id==submission_id).order_by(VerdictAttempt.attempt_number.asc())).all()
