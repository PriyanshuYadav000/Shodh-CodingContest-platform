from datetime import datetime
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator
)

from shodh.models.contest import ContestStatus


class ContestCreateRequest(BaseModel):

    title: str = Field(min_length=3, max_length=180)
    slug: str = Field(min_length=3, max_length=120)
    description: str | None = None

    registration_opens_at: AwareDatetime
    starts_at: AwareDatetime
    ends_at: AwareDatetime

    wrong_attempt_penalty_minutes: int = Field(
        default=20,
        ge=0,
        le=1440
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        return value.strip()

    @field_validator("slug")
    @classmethod
    def validate_slug(cls, value: str) -> str:
        value = value.strip().lower()

        if not value.replace("-", "").isalnum():
            raise ValueError("Invalid contest slug")

        return value

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
    description: str | None = None

    registration_opens_at: AwareDatetime | None = None
    starts_at: AwareDatetime | None = None
    ends_at: AwareDatetime | None = None

    wrong_attempt_penalty_minutes: int | None = Field(
        default=None,
        ge=0,
        le=1440
    )


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
    