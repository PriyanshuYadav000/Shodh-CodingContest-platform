from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException

from shodh.models.contest import ContestStatus
from shodh.models.membership import MembershipRole
from shodh.services import contest_service


@pytest.mark.parametrize(
    "status",
    [ContestStatus.DRAFT, ContestStatus.CANCELLED],
)
def test_participant_cannot_view_unpublished_or_cancelled_contest(
    monkeypatch: pytest.MonkeyPatch,
    status: ContestStatus,
) -> None:
    contest = SimpleNamespace(status=status)
    monkeypatch.setattr(
        contest_service,
        "get_contest_by_id",
        lambda *args, **kwargs: contest,
    )

    with pytest.raises(HTTPException) as exc_info:
        contest_service.get_contest_details(
            db=object(),
            organization_id=uuid4(),
            contest_id=uuid4(),
            role=MembershipRole.PARTICIPANT,
        )

    assert exc_info.value.status_code == 404


def test_participant_can_view_published_contest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contest = SimpleNamespace(status=ContestStatus.PUBLISHED)
    monkeypatch.setattr(
        contest_service,
        "get_contest_by_id",
        lambda *args, **kwargs: contest,
    )

    result = contest_service.get_contest_details(
        db=object(),
        organization_id=uuid4(),
        contest_id=uuid4(),
        role=MembershipRole.PARTICIPANT,
    )

    assert result is contest


def test_organizer_can_view_draft_contest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    contest = SimpleNamespace(status=ContestStatus.DRAFT)
    monkeypatch.setattr(
        contest_service,
        "get_contest_by_id",
        lambda *args, **kwargs: contest,
    )

    result = contest_service.get_contest_details(
        db=object(),
        organization_id=uuid4(),
        contest_id=uuid4(),
        role=MembershipRole.ORGANIZER,
    )

    assert result is contest


def test_unknown_contest_returns_not_found(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        contest_service,
        "get_contest_by_id",
        lambda *args, **kwargs: None,
    )

    with pytest.raises(HTTPException) as exc_info:
        contest_service.get_contest_details(
            db=object(),
            organization_id=uuid4(),
            contest_id=uuid4(),
            role=MembershipRole.ORGANIZER,
        )

    assert exc_info.value.status_code == 404
