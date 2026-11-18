from uuid import UUID, uuid4

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from shodh.models.contest import ContestStatus
from shodh.models.membership import MembershipRole
from shodh.models.problem import Problem, ProblemVersion, TestCase, TestSuiteVersion
from shodh.repositories.contest_repository import get_contest_by_id
from shodh.repositories.problem_repository import (
    create_problem,
    get_current_problem_version,
    get_problem_by_id,
    list_problem_versions,
    list_problems,
)
from shodh.schemas.problem import (
    ProblemCreateRequest,
    ProblemUpdateRequest,
    TestCaseRequest,
)


def _not_found() -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Problem not found")


def _require_contest(db: Session, organization_id: UUID, contest_id: UUID):
    contest = get_contest_by_id(db, organization_id, contest_id)
    if contest is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contest not found")
    return contest


def _make_suite(
    problem: Problem,
    problem_version: ProblemVersion,
    creator_id: UUID,
    version_number: int,
    cases: list[TestCaseRequest] | list[TestCase],
) -> TestSuiteVersion:
    suite = TestSuiteVersion(
        problem_id=problem.id,
        problem_version=problem_version,
        version_number=version_number,
        created_by=creator_id,
    )
    for ordinal, case in enumerate(cases, start=1):
        suite.test_cases.append(
            TestCase(
                ordinal=ordinal,
                input_data=case.input_data,
                expected_output=case.expected_output,
                is_hidden=case.is_hidden,
            )
        )
    return suite


def _make_version(
    problem: Problem,
    creator_id: UUID,
    version_number: int,
    payload: ProblemCreateRequest | ProblemUpdateRequest,
    cases: list[TestCaseRequest] | list[TestCase],
) -> ProblemVersion:
    version = ProblemVersion(
        problem=problem,
        version_number=version_number,
        title=payload.title,
        statement=payload.statement,
        input_format=payload.input_format,
        output_format=payload.output_format,
        constraints_text=payload.constraints_text,
        time_limit_ms=payload.time_limit_ms,
        memory_limit_mb=payload.memory_limit_mb,
        created_by=creator_id,
    )
    version.test_suite_version = _make_suite(
        problem, version, creator_id, version_number, cases
    )
    return version


def create_new_problem(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    creator_id: UUID,
    payload: ProblemCreateRequest,
) -> Problem:
    _require_contest(db, organization_id, contest_id)
    problem = Problem(
        id=uuid4(),
        organization_id=organization_id,
        contest_id=contest_id,
        created_by=creator_id,
        slug=payload.slug,
    )
    _make_version(problem, creator_id, 1, payload, payload.test_cases)
    try:
        create_problem(db, problem)
        db.commit()
        db.refresh(problem)
        return problem
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Problem slug already exists in this contest",
        ) from exc


def _load_visible_problem(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
    role: MembershipRole,
) -> Problem:
    contest = _require_contest(db, organization_id, contest_id)
    if role == MembershipRole.PARTICIPANT and contest.status != ContestStatus.PUBLISHED:
        raise _not_found()
    problem = get_problem_by_id(db, organization_id, contest_id, problem_id)
    if problem is None or (
        role == MembershipRole.PARTICIPANT
        and not problem.is_active
    ):
        raise _not_found()
    return problem


def get_problem_details(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
    role: MembershipRole,
) -> tuple[Problem, ProblemVersion]:
    problem = _load_visible_problem(db, organization_id, contest_id, problem_id, role)
    version = get_current_problem_version(db, problem.id)
    if version is None:
        raise _not_found()
    return problem, version


def get_contest_problems(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    role: MembershipRole,
    limit: int,
    offset: int,
) -> dict:
    contest = _require_contest(db, organization_id, contest_id)
    if role == MembershipRole.PARTICIPANT and contest.status != ContestStatus.PUBLISHED:
        return {"items": [], "total": 0, "limit": limit, "offset": offset}
    problems, total = list_problems(
        db, organization_id, contest_id, role == MembershipRole.PARTICIPANT, limit, offset
    )
    items = []
    for problem in problems:
        version = get_current_problem_version(db, problem.id)
        if version is not None:
            items.append((problem, version))
    return {"items": items, "total": total, "limit": limit, "offset": offset}


def update_problem(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
    editor_id: UUID,
    payload: ProblemUpdateRequest,
) -> Problem:
    _require_contest(db, organization_id, contest_id)
    problem = get_problem_by_id(db, organization_id, contest_id, problem_id, for_update=True)
    if problem is None:
        raise _not_found()
    current = get_current_problem_version(db, problem.id)
    if current is None or current.test_suite_version is None:
        raise _not_found()
    cases = payload.test_cases
    if cases is None:
        cases = list(current.test_suite_version.test_cases)
    _make_version(problem, editor_id, current.version_number + 1, payload, cases)
    if payload.slug is not None:
        problem.slug = payload.slug
    try:
        db.commit()
        db.refresh(problem)
        return problem
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Problem slug already exists in this contest or the version could not be created",
        ) from exc


def deactivate_problem(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
) -> Problem:
    _require_contest(db, organization_id, contest_id)
    problem = get_problem_by_id(db, organization_id, contest_id, problem_id, for_update=True)
    if problem is None:
        raise _not_found()
    if not problem.is_active:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Problem is already inactive")
    problem.is_active = False
    db.commit()
    db.refresh(problem)
    return problem


def get_problem_version_history(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
    limit: int,
    offset: int,
) -> dict:
    _require_contest(db, organization_id, contest_id)
    problem = get_problem_by_id(db, organization_id, contest_id, problem_id)
    if problem is None:
        raise _not_found()
    items, total = list_problem_versions(db, problem.id, limit, offset)
    return {"items": items, "total": total, "limit": limit, "offset": offset}
