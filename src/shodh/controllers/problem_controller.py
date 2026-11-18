from uuid import UUID

from sqlalchemy.orm import Session

from shodh.models.membership import MembershipRole
from shodh.models.problem import Problem, ProblemVersion
from shodh.schemas.problem import ProblemCreateRequest, ProblemUpdateRequest
from shodh.services.problem_service import (
    create_new_problem,
    deactivate_problem,
    get_contest_problems,
    get_problem_details,
    get_problem_version_history,
    update_problem,
)


def _serialize_problem(
    problem: Problem,
    version: ProblemVersion,
    role: MembershipRole,
) -> dict:
    response = {
        "id": problem.id,
        "organization_id": problem.organization_id,
        "contest_id": problem.contest_id,
        "created_by": problem.created_by,
        "slug": problem.slug,
        "is_active": problem.is_active,
        "version_number": version.version_number,
        "title": version.title,
        "statement": version.statement,
        "input_format": version.input_format,
        "output_format": version.output_format,
        "constraints_text": version.constraints_text,
        "time_limit_ms": version.time_limit_ms,
        "memory_limit_mb": version.memory_limit_mb,
        "created_at": problem.created_at,
        "updated_at": problem.updated_at,
    }
    cases = version.test_suite_version.test_cases if version.test_suite_version else []
    if role == MembershipRole.ORGANIZER:
        response["test_suite_version_number"] = (
            version.test_suite_version.version_number if version.test_suite_version else 0
        )
        response["test_cases"] = cases
    else:
        # Never serialize hidden case input or expected output for participants.
        response["test_cases"] = [case for case in cases if not case.is_hidden]
    return response


def create_problem_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    creator_id: UUID,
    payload: ProblemCreateRequest,
):
    problem = create_new_problem(db, organization_id, contest_id, creator_id, payload)
    version = get_problem_details(
        db, organization_id, contest_id, problem.id, MembershipRole.ORGANIZER
    )[1]
    return _serialize_problem(problem, version, MembershipRole.ORGANIZER)


def list_problems_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    role: MembershipRole,
    limit: int,
    offset: int,
):
    page = get_contest_problems(db, organization_id, contest_id, role, limit, offset)
    page["items"] = [_serialize_problem(problem, version, role) for problem, version in page["items"]]
    return page


def get_problem_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
    role: MembershipRole,
):
    problem, version = get_problem_details(db, organization_id, contest_id, problem_id, role)
    return _serialize_problem(problem, version, role)


def update_problem_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
    editor_id: UUID,
    payload: ProblemUpdateRequest,
):
    problem = update_problem(db, organization_id, contest_id, problem_id, editor_id, payload)
    version = get_problem_details(
        db, organization_id, contest_id, problem.id, MembershipRole.ORGANIZER
    )[1]
    return _serialize_problem(problem, version, MembershipRole.ORGANIZER)


def deactivate_problem_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
):
    problem = deactivate_problem(db, organization_id, contest_id, problem_id)
    version = get_problem_details(
        db, organization_id, contest_id, problem.id, MembershipRole.ORGANIZER
    )[1]
    return _serialize_problem(problem, version, MembershipRole.ORGANIZER)


def list_problem_versions_controller(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
    limit: int,
    offset: int,
):
    return get_problem_version_history(db, organization_id, contest_id, problem_id, limit, offset)
