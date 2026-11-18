import re
from datetime import datetime
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from shodh.models.contest import ContestStatus


def _normalize_title(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()
    if len(value) < 3:
        raise ValueError("Contest title must contain at least 3 characters")

    return value


def _normalize_slug(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip().lower()
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError(
            "Slug must contain lowercase letters and numbers separated "
            "by single hyphens"
        )

    return value


class ContestCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    slug: str = Field(min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=10000)

    registration_opens_at: AwareDatetime
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    wrong_attempt_penalty_minutes: int = Field(
        default=20,
        ge=0,
        le=1440,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = _normalize_title(value)
        assert normalized is not None
        return normalized

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        normalized = _normalize_slug(value)
        assert normalized is not None
        return normalized

    @model_validator(mode="after")
    def validate_schedule(self):
        if not (
            self.registration_opens_at
            < self.starts_at
            < self.ends_at
        ):
            raise ValueError(
                "Schedule must satisfy registration open < start < end"
            )
        return self


class ContestUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=180)
    slug: str | None = Field(default=None, min_length=3, max_length=120)
    description: str | None = Field(default=None, max_length=10000)

    registration_opens_at: AwareDatetime | None = None
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None

    wrong_attempt_penalty_minutes: int | None = Field(
        default=None,
        ge=0,
        le=1440,
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        return _normalize_title(value)

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str | None) -> str | None:
        return _normalize_slug(value)


class ContestResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    organization_id: UUID
    created_by: UUID
    title: str
    slug: str
    description: str | None
    status: ContestStatus
    registration_opens_at: datetime
    starts_at: datetime
    ends_at: datetime
    wrong_attempt_penalty_minutes: int
    created_at: datetime
    updated_at: datetime


class ContestPageResponse(BaseModel):
    items: list[ContestResponse]
    total: int
    limit: int
    offset: int
