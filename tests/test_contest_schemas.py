from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from shodh.schemas.contest import ContestCreateRequest, ContestUpdateRequest


def valid_contest_payload() -> dict:
    registration_opens_at = datetime.now(UTC) + timedelta(days=1)
    starts_at = registration_opens_at + timedelta(days=1)
    ends_at = starts_at + timedelta(hours=2)

    return {
        "title": "Spring Contest",
        "slug": "spring-contest",
        "registration_opens_at": registration_opens_at,
        "starts_at": starts_at,
        "ends_at": ends_at,
    }


def test_create_normalizes_title_and_slug() -> None:
    payload = valid_contest_payload()
    payload["title"] = "  Spring Contest  "
    payload["slug"] = "  Spring-Contest  "

    contest = ContestCreateRequest.model_validate(payload)

    assert contest.title == "Spring Contest"
    assert contest.slug == "spring-contest"


@pytest.mark.parametrize(
    "slug",
    [
        "--spring",
        "spring--contest",
        "-spring",
        "spring-",
        "spring_contest",
        "sp",
    ],
)
def test_create_rejects_malformed_slugs(slug: str) -> None:
    payload = valid_contest_payload()
    payload["slug"] = slug

    with pytest.raises(ValidationError):
        ContestCreateRequest.model_validate(payload)


def test_create_rejects_title_that_is_blank_after_trimming() -> None:
    payload = valid_contest_payload()
    payload["title"] = "   "

    with pytest.raises(ValidationError):
        ContestCreateRequest.model_validate(payload)


def test_create_requires_timezone_aware_schedule() -> None:
    payload = valid_contest_payload()
    payload["registration_opens_at"] = datetime(2027, 1, 1)
    payload["starts_at"] = datetime(2027, 1, 2)
    payload["ends_at"] = datetime(2027, 1, 3)

    with pytest.raises(ValidationError):
        ContestCreateRequest.model_validate(payload)


def test_update_applies_same_slug_normalization_and_validation() -> None:
    update = ContestUpdateRequest(slug="  Spring-Contest  ")

    assert update.slug == "spring-contest"

    with pytest.raises(ValidationError):
        ContestUpdateRequest(slug="spring--contest")


def test_update_rejects_title_that_is_blank_after_trimming() -> None:
    with pytest.raises(ValidationError):
        ContestUpdateRequest(title="   ")
