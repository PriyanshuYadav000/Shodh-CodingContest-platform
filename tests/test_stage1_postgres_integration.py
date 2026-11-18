from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from shodh.config.settings import settings
from shodh.models.contest import Contest, ContestStatus
from shodh.models.membership import Membership, MembershipRole
from shodh.models.organization import Organization
from shodh.models.participation import Participation
from shodh.models.problem import (
    Problem,
    ProblemVersion,
)
from shodh.models.problem import (
    TestCase as ProblemTestCase,
)
from shodh.models.problem import (
    TestSuiteVersion as ProblemTestSuiteVersion,
)
from shodh.models.submission import SubmissionStatus, VerdictType\nfrom shodh.repositories.submission_repository import claim_next_submission
from shodh.models.user import User
from shodh.schemas.submission import SubmissionCreateRequest, VerdictCreateRequest
from shodh.services.submission_service import (
    create_new_submission,
    get_leaderboard,
    get_submissions,
    get_verdict_history,
    get_visible_submission,
    record_verdict,
)


@pytest.fixture()
def db():
    engine = create_engine(settings.database_url)
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
        engine.dispose()


def setup_contest(db: Session):
    org = Organization(id=uuid4(), name="Integration Org", slug=f"int-{uuid4().hex[:12]}")
    organizer = User(id=uuid4(), full_name="Organizer", email=f"o-{uuid4().hex}@example.test", password_hash="x")
    participant = User(id=uuid4(), full_name="Participant", email=f"p-{uuid4().hex}@example.test", password_hash="x")
    idle = User(id=uuid4(), full_name="Idle", email=f"i-{uuid4().hex}@example.test", password_hash="x")
    now = datetime.now(UTC)
    contest = Contest(organization_id=org.id, created_by=organizer.id, title="Integration Contest", slug=f"contest-{uuid4().hex[:8]}", status=ContestStatus.PUBLISHED, registration_opens_at=now-timedelta(days=1), starts_at=now-timedelta(minutes=30), ends_at=now+timedelta(hours=1), wrong_attempt_penalty_minutes=20)
    db.add_all([org, organizer, participant, idle]); db.flush()
    db.add_all([Membership(organization_id=org.id,user_id=organizer.id,role=MembershipRole.ORGANIZER), Membership(organization_id=org.id,user_id=participant.id,role=MembershipRole.PARTICIPANT), Membership(organization_id=org.id,user_id=idle.id,role=MembershipRole.PARTICIPANT), contest]); db.flush()
    problem = Problem(id=uuid4(), organization_id=org.id, contest_id=contest.id, created_by=organizer.id, slug=f"problem-{uuid4().hex[:8]}", legacy_title="P", legacy_statement="s", legacy_input_format="i", legacy_output_format="o", legacy_time_limit_ms=1000, legacy_memory_limit_mb=256, legacy_points=100)
    version = ProblemVersion(problem=problem,version_number=1,title="P",statement="s",input_format="i",output_format="o",time_limit_ms=1000,memory_limit_mb=256,created_by=organizer.id)
    suite = ProblemTestSuiteVersion(problem_id=problem.id,problem_version=version,version_number=1,created_by=organizer.id)
    suite.test_cases.extend([ProblemTestCase(ordinal=1,input_data="1",expected_output="1",is_hidden=False),ProblemTestCase(ordinal=2,input_data="2",expected_output="2",is_hidden=True)])
    db.add_all([problem, Participation(contest_id=contest.id,user_id=participant.id), Participation(contest_id=contest.id,user_id=idle.id)]); db.commit()
    return org, contest, participant, organizer, idle, problem, version, suite


def test_submission_pinning_access_verdicts_and_leaderboard(db: Session) -> None:
    org, contest, participant, organizer, idle, problem, version, suite = setup_contest(db)
    submission = create_new_submission(db, org.id, contest.id, participant.id, SubmissionCreateRequest(problem_id=problem.id,source_code="print(1)",language="python"))
    assert (submission.problem_version_id, submission.test_suite_version_id) == (version.id, suite.id)
    assert get_visible_submission(db,org.id,contest.id,submission.id,participant.id,MembershipRole.PARTICIPANT).id == submission.id
    assert get_submissions(db,org.id,contest.id,organizer.id,MembershipRole.ORGANIZER,20,0)["total"] == 1
    first = record_verdict(db,submission.id,VerdictCreateRequest(verdict=VerdictType.WRONG_ANSWER,total_tests=2))
    second = record_verdict(db,submission.id,VerdictCreateRequest(verdict=VerdictType.ACCEPTED,passed_tests=2,total_tests=2))
    history = get_verdict_history(db,org.id,contest.id,submission.id,participant.id,MembershipRole.PARTICIPANT)
    assert [attempt.attempt_number for attempt in history] == [1, 2]
    board = get_leaderboard(db,org.id,contest.id,20,0)
    assert board["total"] == 2
    winner = next(row for row in board["items"] if row["user_id"] == participant.id)
    zero = next(row for row in board["items"] if row["user_id"] == idle.id)
    assert winner["score"] == 100 and winner["penalty_minutes"] >= 20
    assert zero["score"] == zero["solved"] == zero["penalty_minutes"] == 0
    assert first.id != second.id



def test_claim_next_submission_changes_queued_to_running(db: Session) -> None:
    org, contest, participant, _, _, problem, _, _ = setup_contest(db)
    submission = create_new_submission(
        db,
        org.id,
        contest.id,
        participant.id,
        SubmissionCreateRequest(
            problem_id=problem.id,
            source_code="print(1)",
            language="python",
        ),
    )

    assert submission.status == SubmissionStatus.QUEUED
    assert submission.started_at is None

    claimed = claim_next_submission(db)

    assert claimed is not None
    assert claimed.id == submission.id
    assert claimed.status == SubmissionStatus.RUNNING
    assert claimed.started_at is not None
    assert claimed.completed_at is None
    assert claim_next_submission(db) is None


def test_claim_next_submission_returns_none_for_empty_queue(db: Session) -> None:
    assert claim_next_submission(db) is None
