"""Deterministic development seed data: run with ``python -m shodh.seed``."""
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from shodh.database.session import SessionLocal
from shodh.models.contest import Contest, ContestStatus
from shodh.models.membership import Membership, MembershipRole
from shodh.models.organization import Organization
from shodh.models.problem import Problem, ProblemVersion, TestCase, TestSuiteVersion
from shodh.models.user import User
from shodh.security.password import hash_password

ORGA = UUID("00000000-0000-0000-0000-000000000001")
ORGB = UUID("00000000-0000-0000-0000-000000000002")
ORGANIZER = UUID("00000000-0000-0000-0000-000000000011")
PARTICIPANT = UUID("00000000-0000-0000-0000-000000000012")

def main() -> None:
    db = SessionLocal()
    try:
        if db.get(Organization, ORGA): return
        organizer=User(id=ORGANIZER,full_name="Demo Organizer",email="organizer@example.test",password_hash=hash_password("OrganizerPass123!"))
        participant=User(id=PARTICIPANT,full_name="Demo Participant",email="participant@example.test",password_hash=hash_password("ParticipantPass123!"))
        first=Organization(id=ORGA,name="Shodh Academy",slug="shodh-academy"); second=Organization(id=ORGB,name="Example Institute",slug="example-institute")
        db.add_all([organizer, participant, first, second]); db.flush()
        db.add_all([Membership(organization_id=ORGA,user_id=ORGANIZER,role=MembershipRole.ORGANIZER),Membership(organization_id=ORGA,user_id=PARTICIPANT,role=MembershipRole.PARTICIPANT),Membership(organization_id=ORGB,user_id=ORGANIZER,role=MembershipRole.ORGANIZER)])
        now=datetime.now(UTC); contests=[Contest(organization_id=ORGA,created_by=ORGANIZER,title="Seed Open Contest",slug="seed-open",status=ContestStatus.PUBLISHED,registration_opens_at=now-timedelta(days=2),starts_at=now-timedelta(hours=1),ends_at=now+timedelta(days=1)),Contest(organization_id=ORGB,created_by=ORGANIZER,title="Seed Draft Contest",slug="seed-draft",status=ContestStatus.DRAFT,registration_opens_at=now+timedelta(days=1),starts_at=now+timedelta(days=2),ends_at=now+timedelta(days=3))]
        db.add_all(contests); db.flush()
        for number,title in enumerate(("Sum", "Maximum", "Palindrome"),1):
            problem=Problem(id=uuid4(),organization_id=ORGA,contest_id=contests[0].id,created_by=ORGANIZER,slug=f"seed-{number}",legacy_title=title,legacy_statement="Seed statement",legacy_input_format="input",legacy_output_format="output",legacy_time_limit_ms=1000,legacy_memory_limit_mb=256,legacy_points=100)
            version=ProblemVersion(problem=problem,version_number=1,title=title,statement="Seed statement",input_format="input",output_format="output",time_limit_ms=1000,memory_limit_mb=256,created_by=ORGANIZER)
            suite=TestSuiteVersion(problem_id=problem.id,problem_version=version,version_number=1,created_by=ORGANIZER)
            suite.test_cases.extend([TestCase(ordinal=1,input_data="1\n",expected_output="1\n",is_hidden=False),TestCase(ordinal=2,input_data="2\n",expected_output="2\n",is_hidden=True)])
            db.add(problem)
        db.commit()
    finally: db.close()
if __name__ == "__main__": main()
