from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from shodh.models.contest import ContestStatus
from shodh.services import participation_service


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


def published_contest(**overrides):
    now = datetime.now(UTC)
    values = {
        "status": ContestStatus.PUBLISHED,
        "registration_opens_at": now - timedelta(hours=1),
        "starts_at": now + timedelta(hours=2),
        "ends_at": now + timedelta(hours=4),
    }
    values.update(overrides)
    return SimpleNamespace(**values)


def patch_registration_repositories(
    monkeypatch: pytest.MonkeyPatch,
    contest,
    existing=None,
    create=None,
) -> None:
    def fake_get_contest(db, organization_id, contest_id, **kwargs):
        assert kwargs.get("read_lock") is True
        return contest

    monkeypatch.setattr(
        participation_service,
        "get_contest_by_id",
        fake_get_contest,
    )
    monkeypatch.setattr(
        participation_service,
        "get_participation",
        lambda *args, **kwargs: existing,
    )

    def fake_create(db, participation):
        if create is not None:
            return create(db, participation)
        db.add(participation)
        db.flush()
        return participation

    monkeypatch.setattr(
        participation_service,
        "create_participation",
        fake_create,
    )


def test_registers_participant_during_registration_window(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = FakeSession()
    contest_id = uuid4()
    user_id = uuid4()
    patch_registration_repositories(
        monkeypatch,
        published_contest(),
    )

    result = participation_service.register_for_contest(
        db,
        uuid4(),
        contest_id,
        user_id,
    )

    assert result.contest_id == contest_id
    assert result.user_id == user_id
    assert db.committed is True
    assert db.rolled_back is False


@pytest.mark.parametrize(
    "contest",
    [
        published_contest(status=ContestStatus.DRAFT),
        published_contest(status=ContestStatus.CANCELLED),
    ],
)
def test_rejects_contest_that_is_not_published(
    monkeypatch: pytest.MonkeyPatch,
    contest,
) -> None:
    db = FakeSession()
    patch_registration_repositories(monkeypatch, contest)

    with pytest.raises(HTTPException) as exc_info:
        participation_service.register_for_contest(
            db,
            uuid4(),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 409
    assert db.committed is False


def test_rejects_registration_before_opening(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = FakeSession()
    opens_at = datetime.now(UTC) + timedelta(hours=1)
    contest = published_contest(
        registration_opens_at=opens_at,
        starts_at=opens_at + timedelta(hours=1),
        ends_at=opens_at + timedelta(hours=2),
    )
    patch_registration_repositories(monkeypatch, contest)

    with pytest.raises(HTTPException) as exc_info:
        participation_service.register_for_contest(
            db,
            uuid4(),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 409


def test_rejects_registration_after_contest_starts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = FakeSession()
    contest = published_contest(
        starts_at=datetime.now(UTC) - timedelta(seconds=1),
    )
    patch_registration_repositories(monkeypatch, contest)

    with pytest.raises(HTTPException) as exc_info:
        participation_service.register_for_contest(
            db,
            uuid4(),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 409


def test_rejects_duplicate_registration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = FakeSession()
    patch_registration_repositories(
        monkeypatch,
        published_contest(),
        existing=object(),
    )

    with pytest.raises(HTTPException) as exc_info:
        participation_service.register_for_contest(
            db,
            uuid4(),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 409
    assert db.committed is False


def test_handles_concurrent_duplicate_insert(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = FakeSession()

    def raise_integrity_error(db, participation):
        raise IntegrityError("INSERT", {}, Exception("duplicate key"))

    patch_registration_repositories(
        monkeypatch,
        published_contest(),
        create=raise_integrity_error,
    )

    with pytest.raises(HTTPException) as exc_info:
        participation_service.register_for_contest(
            db,
            uuid4(),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 409
    assert db.rolled_back is True


def test_returns_not_found_for_unknown_contest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    db = FakeSession()

    def fake_get_contest(*args, **kwargs):
        return None

    monkeypatch.setattr(
        participation_service,
        "get_contest_by_id",
        fake_get_contest,
    )

    with pytest.raises(HTTPException) as exc_info:
        participation_service.register_for_contest(
            db,
            uuid4(),
            uuid4(),
            uuid4(),
        )

    assert exc_info.value.status_code == 404
