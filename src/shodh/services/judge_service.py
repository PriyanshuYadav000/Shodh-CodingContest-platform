from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from shodh.models.problem import (
    ProblemVersion,
    TestCase,
    TestSuiteVersion,
)
from shodh.models.submission import (
    Submission,
    SubmissionStatus,
    VerdictType,
)
from shodh.schemas.submission import VerdictCreateRequest
from shodh.services.code_runner import RunnerStatus, run_python
from shodh.services.submission_service import record_verdict


def _normalize_output(output: str) -> str:
    """Ignore surrounding whitespace and normalize line endings."""
    return output.replace("\r\n", "\n").replace("\r", "\n").strip()


def _record_infrastructure_error(
    db: Session,
    submission_id: UUID,
    total_tests: int = 0,
):
    return record_verdict(
        db,
        submission_id,
        VerdictCreateRequest(
            verdict=VerdictType.INFRASTRUCTURE_ERROR,
            passed_tests=0,
            total_tests=total_tests,
            diagnostics="Judge infrastructure error.",
        ),
    )


def judge_submission(
    db: Session,
    submission_id: UUID,
):
    """
    Judge a claimed submission using its exact pinned
    problem and test-suite versions.
    """

    submission = db.get(Submission, submission_id)

    if submission is None:
        raise ValueError("Submission not found")

    if submission.status != SubmissionStatus.RUNNING:
        raise ValueError("Submission must be claimed before judging")

    # Load the exact versions pinned to this submission.
    problem_version = db.get(
        ProblemVersion,
        submission.problem_version_id,
    )

    test_suite = db.get(
        TestSuiteVersion,
        submission.test_suite_version_id,
    )

    if (
        problem_version is None
        or test_suite is None
        or problem_version.problem_id != submission.problem_id
        or test_suite.problem_id != submission.problem_id
        or test_suite.problem_version_id != problem_version.id
    ):
        return _record_infrastructure_error(db, submission_id)

    # Load all visible and hidden test cases.
    test_cases = db.scalars(
        select(TestCase)
        .where(
            TestCase.test_suite_version_id == test_suite.id
        )
        .order_by(TestCase.ordinal.asc())
    ).all()

    if not test_cases:
        return _record_infrastructure_error(db, submission_id)

    # Python 3 is the only supported language.
    if submission.language.strip().lower() not in {"python", "python3"}:
        return record_verdict(
            db,
            submission_id,
            VerdictCreateRequest(
                verdict=VerdictType.COMPILATION_ERROR,
                total_tests=len(test_cases),
                diagnostics="Only Python 3 submissions are supported.",
            ),
        )

    passed_tests = 0
    total_execution_time = 0

    verdict_mapping = {
        RunnerStatus.COMPILATION_ERROR: VerdictType.COMPILATION_ERROR,
        RunnerStatus.RUNTIME_ERROR: VerdictType.RUNTIME_ERROR,
        RunnerStatus.TIME_LIMIT_EXCEEDED: VerdictType.TIME_LIMIT_EXCEEDED,
        RunnerStatus.MEMORY_LIMIT_EXCEEDED: VerdictType.MEMORY_LIMIT_EXCEEDED,
        RunnerStatus.OUTPUT_LIMIT_EXCEEDED: VerdictType.OUTPUT_LIMIT_EXCEEDED,
        RunnerStatus.INFRASTRUCTURE_ERROR: VerdictType.INFRASTRUCTURE_ERROR,
    }

    final_verdict = VerdictType.ACCEPTED

    # Execute cases in ordinal order.
    for test_case in test_cases:

        result = run_python(
            source_code=submission.source_code,
            stdin=test_case.input_data,
            time_limit_ms=problem_version.time_limit_ms,
            memory_limit_mb=problem_version.memory_limit_mb,
        )

        total_execution_time += result.execution_time_ms

        if result.status != RunnerStatus.COMPLETED:
            final_verdict = verdict_mapping[result.status]
            break

        actual_output = _normalize_output(result.stdout)
        expected_output = _normalize_output(test_case.expected_output)

        if actual_output != expected_output:
            final_verdict = VerdictType.WRONG_ANSWER
            break

        passed_tests += 1

    # Never store actual or expected test contents in diagnostics.
    diagnostics = None

    if final_verdict == VerdictType.INFRASTRUCTURE_ERROR:
        diagnostics = "Judge infrastructure error."

    return record_verdict(
        db,
        submission_id,
        VerdictCreateRequest(
            verdict=final_verdict,
            passed_tests=passed_tests,
            total_tests=len(test_cases),
            execution_time_ms=total_execution_time,
            diagnostics=diagnostics,
        ),
    )