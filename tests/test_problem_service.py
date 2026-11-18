from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from shodh.controllers.problem_controller import _serialize_problem
from shodh.dependencies.organization import require_organization_role
from shodh.models.contest import ContestStatus
from shodh.models.membership import MembershipRole
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
from shodh.schemas.problem import ProblemCreateRequest, ProblemUpdateRequest
from shodh.services import problem_service


class FakeSession:
    def __init__(self) -> None:
        self.added = []
        self.committed = False
        self.rolled_back = False

    def add(self, item) -> None:
        self.added.append(item)

    def flush(self) -> None:
        return None

    def commit(self) -> None:
        self.committed = True

    def refresh(self, item) -> None:
        return None

    def rollback(self) -> None:
        self.rolled_back = True


def create_payload() -> ProblemCreateRequest:
    return ProblemCreateRequest(
        slug="sum-two-values",
        title="Sum two values",
        statement="Read two integers and print their sum.",
        time_limit_ms=1000,
        memory_limit_mb=256,
        test_cases=[
            {"input_data": "1 2\n", "expected_output": "3\n", "is_hidden": False},
            {"input_data": "99 1\n", "expected_output": "100\n", "is_hidden": True},
        ],
    )


def update_payload() -> ProblemUpdateRequest:
    payload = create_payload().model_dump()
    payload.pop("slug")
    payload["title"] = "Add two values"
    payload.pop("test_cases")
    return ProblemUpdateRequest(**payload)


def make_versioned_problem() -> tuple[Problem, ProblemVersion]:
    problem = Problem(
        id=uuid4(),
        organization_id=uuid4(),
        contest_id=uuid4(),
        created_by=uuid4(),
        slug="sum-two-values",
        is_active=True,
    )
    version = ProblemVersion(
        problem=problem,
        version_number=1,
        title="Sum two values",
        statement="Read two integers and print their sum.",
        time_limit_ms=1000,
        memory_limit_mb=256,
        created_by=problem.created_by,
    )
    suite = ProblemTestSuiteVersion(
        problem_id=problem.id,
        problem_version=version,
        version_number=1,
        created_by=problem.created_by,
    )
    suite.test_cases.extend(
        [
            ProblemTestCase(ordinal=1, input_data="1 2\n", expected_output="3\n", is_hidden=False),
            ProblemTestCase(ordinal=2, input_data="99 1\n", expected_output="100\n", is_hidden=True),
        ]
    )
    return problem, version


def test_creation_rolls_back_on_duplicate_slug(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeSession()
    monkeypatch.setattr(problem_service, "get_contest_by_id", lambda *args: object())

    def duplicate(*args):
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    monkeypatch.setattr(problem_service, "create_problem", duplicate)
    with pytest.raises(HTTPException) as exc_info:
        problem_service.create_new_problem(db, uuid4(), uuid4(), uuid4(), create_payload())

    assert exc_info.value.status_code == 409
    assert db.rolled_back is True
    assert db.committed is False


def test_creation_rejects_contest_outside_organization(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(problem_service, "get_contest_by_id", lambda *args: None)
    with pytest.raises(HTTPException) as exc_info:
        problem_service.create_new_problem(FakeSession(), uuid4(), uuid4(), uuid4(), create_payload())
    assert exc_info.value.status_code == 404


def test_update_preserves_previous_version_and_test_suite(monkeypatch: pytest.MonkeyPatch) -> None:
    db = FakeSession()
    problem, old_version = make_versioned_problem()
    monkeypatch.setattr(problem_service, "get_contest_by_id", lambda *args: object())
    monkeypatch.setattr(problem_service, "get_problem_by_id", lambda *args, **kwargs: problem)
    monkeypatch.setattr(problem_service, "get_current_problem_version", lambda *args: old_version)

    result = problem_service.update_problem(
        db,
        problem.organization_id,
        problem.contest_id,
        problem.id,
        uuid4(),
        update_payload(),
    )

    assert result is problem
    assert db.committed is True
    assert len(problem.versions) == 2
    new_version = problem.versions[-1]
    assert old_version.title == "Sum two values"
    assert new_version.title == "Add two values"
    assert new_version.version_number == 2
    assert new_version.test_suite_version.version_number == 2
    assert [case.input_data for case in old_version.test_suite_version.test_cases] == ["1 2\n", "99 1\n"]
    assert [case.input_data for case in new_version.test_suite_version.test_cases] == ["1 2\n", "99 1\n"]
    assert new_version.test_suite_version.test_cases[0] is not old_version.test_suite_version.test_cases[0]


def test_update_rolls_back_when_database_rejects_the_new_version(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FailingCommitSession(FakeSession):
        def commit(self) -> None:
            raise IntegrityError("INSERT", {}, Exception("constraint violation"))

    db = FailingCommitSession()
    problem, old_version = make_versioned_problem()
    monkeypatch.setattr(problem_service, "get_contest_by_id", lambda *args: object())
    monkeypatch.setattr(problem_service, "get_problem_by_id", lambda *args, **kwargs: problem)
    monkeypatch.setattr(problem_service, "get_current_problem_version", lambda *args: old_version)

    with pytest.raises(HTTPException) as exc_info:
        problem_service.update_problem(
            db,
            problem.organization_id,
            problem.contest_id,
            problem.id,
            uuid4(),
            update_payload(),
        )

    assert exc_info.value.status_code == 409
    assert db.rolled_back is True


@pytest.mark.parametrize("contest_status", [ContestStatus.DRAFT, ContestStatus.CANCELLED])
def test_participant_cannot_see_problems_of_non_public_contest(
    monkeypatch: pytest.MonkeyPatch, contest_status: ContestStatus
) -> None:
    monkeypatch.setattr(problem_service, "get_contest_by_id", lambda *args: SimpleNamespace(status=contest_status))
    with pytest.raises(HTTPException) as exc_info:
        problem_service.get_problem_details(object(), uuid4(), uuid4(), uuid4(), MembershipRole.PARTICIPANT)
    assert exc_info.value.status_code == 404


def test_participant_cannot_see_inactive_problem(monkeypatch: pytest.MonkeyPatch) -> None:
    problem, _ = make_versioned_problem()
    problem.is_active = False
    monkeypatch.setattr(problem_service, "get_contest_by_id", lambda *args: SimpleNamespace(status=ContestStatus.PUBLISHED))
    monkeypatch.setattr(problem_service, "get_problem_by_id", lambda *args, **kwargs: problem)
    with pytest.raises(HTTPException) as exc_info:
        problem_service.get_problem_details(object(), problem.organization_id, problem.contest_id, problem.id, MembershipRole.PARTICIPANT)
    assert exc_info.value.status_code == 404


def test_participant_serialization_never_includes_hidden_test_case_data() -> None:
    problem, version = make_versioned_problem()
    problem.created_at = problem.updated_at = SimpleNamespace()  # values are not inspected here
    response = _serialize_problem(problem, version, MembershipRole.PARTICIPANT)
    assert response["test_cases"] == [version.test_suite_version.test_cases[0]]
    assert all(not case.is_hidden for case in response["test_cases"])


def test_organizer_serialization_includes_full_test_suite() -> None:
    problem, version = make_versioned_problem()
    problem.created_at = problem.updated_at = SimpleNamespace()
    response = _serialize_problem(problem, version, MembershipRole.ORGANIZER)
    assert len(response["test_cases"]) == 2
    assert response["test_suite_version_number"] == 1


def test_participant_cannot_use_organizer_problem_mutation_dependency() -> None:
    checker = require_organization_role(MembershipRole.ORGANIZER)
    participant_membership = SimpleNamespace(role=MembershipRole.PARTICIPANT)
    with pytest.raises(HTTPException) as exc_info:
        checker(membership=participant_membership)
    assert exc_info.value.status_code == 403
