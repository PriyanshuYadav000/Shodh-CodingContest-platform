from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shodh.models.contest import ContestStatus
from shodh.models.membership import MembershipRole
from shodh.models.participation import Participation
from shodh.models.submission import (
 Submission,
 SubmissionStatus,
 VerdictAttempt,
 VerdictType,
)
from shodh.models.user import User
from shodh.repositories.contest_repository import get_contest_by_id
from shodh.repositories.participation_repository import get_participation
from shodh.repositories.problem_repository import (
 get_current_problem_version,
 get_problem_by_id,
)
from shodh.repositories.submission_repository import (
 create_attempt,
 create_submission,
 get_submission,
 list_attempts,
 list_submissions,
 next_attempt_number,
)
from shodh.schemas.submission import SubmissionCreateRequest, VerdictCreateRequest


def _contest(db, org, contest):
 c=get_contest_by_id(db,org,contest)
 if not c: raise HTTPException(404,"Contest not found")
 return c
def create_new_submission(db:Session,org:UUID,contest_id:UUID,user_id:UUID,payload:SubmissionCreateRequest):
 c=_contest(db,org,contest_id)
 if c.status != ContestStatus.PUBLISHED or datetime.now(UTC) < c.starts_at or datetime.now(UTC) >= c.ends_at: raise HTTPException(409,"Contest is not accepting submissions")
 if not get_participation(db,contest_id,user_id): raise HTTPException(403,"Contest registration required")
 p=get_problem_by_id(db,org,contest_id,payload.problem_id)
 if not p or not p.is_active: raise HTTPException(404,"Problem not found")
 v=get_current_problem_version(db,p.id)
 if not v or not v.test_suite_version: raise HTTPException(409,"Problem is not ready")
 item=Submission(organization_id=org,contest_id=contest_id,problem_id=p.id,problem_version_id=v.id,test_suite_version_id=v.test_suite_version.id,user_id=user_id,source_code=payload.source_code,language=payload.language,runtime_config=payload.runtime_config)
 try:
  create_submission(db,item);db.commit();db.refresh(item);return item
 except IntegrityError as exc: db.rollback();raise HTTPException(409,"Submission could not be saved") from exc
def get_visible_submission(db,org,contest,submission_id,user_id,role):
 _contest(db,org,contest);s=get_submission(db,submission_id)
 if not s or s.organization_id!=org or s.contest_id!=contest or (role==MembershipRole.PARTICIPANT and s.user_id!=user_id): raise HTTPException(404,"Submission not found")
 return s
def get_submissions(db,org,contest,user_id,role,limit,offset):
 _contest(db,org,contest);items,total=list_submissions(db,contest,user_id if role==MembershipRole.PARTICIPANT else None,limit,offset);return {"items":items,"total":total,"limit":limit,"offset":offset}
def record_verdict(db:Session,submission_id:UUID,payload:VerdictCreateRequest):
 s=get_submission(db,submission_id)
 if not s: raise HTTPException(404,"Submission not found")
 if payload.passed_tests>payload.total_tests: raise HTTPException(422,"Passed tests cannot exceed total tests")
 a=VerdictAttempt(submission_id=s.id,attempt_number=next_attempt_number(db,s.id),**payload.model_dump())
 try:
  create_attempt(db,a);s.status=SubmissionStatus.JUDGED;db.commit();db.refresh(a);return a
 except IntegrityError as exc: db.rollback();raise HTTPException(409,"Verdict could not be recorded") from exc
def get_verdict_history(db,org,contest,submission_id,user_id,role):
 get_visible_submission(db,org,contest,submission_id,user_id,role);return list_attempts(db,submission_id)

def get_leaderboard(db, org, contest_id, limit, offset):
 contest = _contest(db, org, contest_id)
 entries = []
 for participation in db.scalars(select(Participation).where(Participation.contest_id == contest_id)):
  user = db.get(User, participation.user_id); score = solved = penalty = 0; last_accepted = None
  submissions = db.scalars(select(Submission).where(Submission.contest_id == contest_id, Submission.user_id == user.id).order_by(Submission.created_at, Submission.id)).all()
  problems = {}
  for submission in submissions: problems.setdefault(submission.problem_id, []).append(submission)
  for problem_submissions in problems.values():
   attempts = [attempt for submission in problem_submissions for attempt in list_attempts(db, submission.id) if attempt.verdict != VerdictType.INFRASTRUCTURE_ERROR]
   accepted = next((attempt for attempt in attempts if attempt.verdict == VerdictType.ACCEPTED), None)
   if accepted:
    solved += 1; score += 100
    wrong = sum(attempt.verdict != VerdictType.ACCEPTED and attempt.created_at <= accepted.created_at for attempt in attempts)
    penalty += max(0, int((accepted.created_at - contest.starts_at).total_seconds() // 60)) + wrong * contest.wrong_attempt_penalty_minutes
    if last_accepted is None or accepted.created_at > last_accepted: last_accepted = accepted.created_at
  entries.append({"user_id": user.id, "full_name": user.full_name, "score": score, "solved": solved, "penalty_minutes": penalty, "last": last_accepted})
 entries.sort(key=lambda entry: (-entry["score"], -entry["solved"], entry["penalty_minutes"], entry["last"] or datetime.max.replace(tzinfo=UTC), str(entry["user_id"])))
 return {"items": [{key: value for key, value in entry.items() if key != "last"} for entry in entries[offset:offset + limit]], "total": len(entries), "limit": limit, "offset": offset}
