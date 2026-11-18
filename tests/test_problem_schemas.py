import pytest
from pydantic import ValidationError

from shodh.schemas.problem import ProblemCreateRequest, ProblemUpdateRequest


def valid_payload() -> dict:
    return {
        "slug": "sum-two-values",
        "title": "Sum two values",
        "statement": "Read two integers and print their sum.",
        "input_format": "Two integers.",
        "output_format": "Their sum.",
        "constraints_text": "Values fit in signed 32-bit integers.",
        "time_limit_ms": 1_000,
        "memory_limit_mb": 256,
        "test_cases": [
            {"input_data": "1 2\n", "expected_output": "3\n", "is_hidden": False},
            {"input_data": "4 5\n", "expected_output": "9\n", "is_hidden": True},
        ],
    }


def test_problem_create_normalizes_slug_and_content() -> None:
    payload = valid_payload()
    payload["slug"] = "  Sum-Two-Values  "
    payload["title"] = "  Sum two values  "

    problem = ProblemCreateRequest.model_validate(payload)

    assert problem.slug == "sum-two-values"
    assert problem.title == "Sum two values"


@pytest.mark.parametrize("slug", ["ab", "bad_slug", "bad--slug", "-bad", "bad-"])
def test_problem_create_rejects_invalid_slugs(slug: str) -> None:
    payload = valid_payload()
    payload["slug"] = slug
    with pytest.raises(ValidationError):
        ProblemCreateRequest.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [("time_limit_ms", 49), ("time_limit_ms", 30_001), ("memory_limit_mb", 15), ("memory_limit_mb", 1_025)],
)
def test_problem_create_rejects_resource_limit_violations(field: str, value: int) -> None:
    payload = valid_payload()
    payload[field] = value
    with pytest.raises(ValidationError):
        ProblemCreateRequest.model_validate(payload)


def test_problem_update_can_omit_test_cases_to_copy_previous_suite() -> None:
    payload = valid_payload()
    payload.pop("slug")
    payload.pop("test_cases")
    update = ProblemUpdateRequest.model_validate(payload)
    assert update.test_cases is None


def test_problem_update_normalizes_a_new_slug() -> None:
    payload = valid_payload()
    payload.pop("slug")
    payload.pop("test_cases")
    payload["slug"] = "  Sum-Again  "
    update = ProblemUpdateRequest.model_validate(payload)
    assert update.slug == "sum-again"
