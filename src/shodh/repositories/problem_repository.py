from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from shodh.models.problem import Problem, ProblemVersion, TestSuiteVersion


def create_problem(db: Session, problem: Problem) -> Problem:
    db.add(problem)
    db.flush()
    return problem


def get_problem_by_id(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    problem_id: UUID,
    for_update: bool = False,
) -> Problem | None:
    statement = select(Problem).where(
        Problem.id == problem_id,
        Problem.organization_id == organization_id,
        Problem.contest_id == contest_id,
    )
    if for_update:
        statement = statement.with_for_update()
    return db.scalar(statement)


def get_current_problem_version(db: Session, problem_id: UUID) -> ProblemVersion | None:
    statement = (
        select(ProblemVersion)
        .where(ProblemVersion.problem_id == problem_id)
        .order_by(ProblemVersion.version_number.desc())
        .limit(1)
        .options(
            joinedload(ProblemVersion.test_suite_version).selectinload(
                TestSuiteVersion.test_cases
            )
        )
    )
    return db.scalar(statement)


def list_problems(
    db: Session,
    organization_id: UUID,
    contest_id: UUID,
    active_only: bool,
    limit: int,
    offset: int,
) -> tuple[list[Problem], int]:
    statement = select(Problem).where(
        Problem.organization_id == organization_id,
        Problem.contest_id == contest_id,
    )
    if active_only:
        statement = statement.where(Problem.is_active.is_(True))
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = db.scalars(
        statement.order_by(Problem.created_at.desc(), Problem.id.asc())
        .limit(limit)
        .offset(offset)
    ).all()
    return items, total


def list_problem_versions(
    db: Session,
    problem_id: UUID,
    limit: int,
    offset: int,
) -> tuple[list[ProblemVersion], int]:
    statement = select(ProblemVersion).where(ProblemVersion.problem_id == problem_id)
    total = db.scalar(select(func.count()).select_from(statement.subquery())) or 0
    items = db.scalars(
        statement.order_by(ProblemVersion.version_number.desc()).limit(limit).offset(offset)
    ).all()
    return items, total
