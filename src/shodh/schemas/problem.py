import re
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

MAX_TEST_CASES = 1_000
MAX_TEST_DATA_LENGTH = 100_000


def _normalize_required_text(value: str, label: str, minimum: int, maximum: int) -> str:
    value = value.strip()
    if not minimum <= len(value) <= maximum:
        raise ValueError(f"{label} must contain between {minimum} and {maximum} characters")
    return value


def _normalize_optional_text(value: str | None, label: str, maximum: int) -> str | None:
    if value is None:
        return None
    value = value.strip()
    if len(value) > maximum:
        raise ValueError(f"{label} must not exceed {maximum} characters")
    return value or None


def _normalize_slug(value: str) -> str:
    value = value.strip().lower()
    if not 3 <= len(value) <= 120:
        raise ValueError("Problem slug must contain between 3 and 120 characters")
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value):
        raise ValueError("Slug must contain lowercase letters and numbers separated by single hyphens")
    return value


class TestCaseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    input_data: str = Field(min_length=1, max_length=MAX_TEST_DATA_LENGTH)
    expected_output: str = Field(min_length=1, max_length=MAX_TEST_DATA_LENGTH)
    is_hidden: bool = True


class ProblemContentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=3, max_length=180)
    statement: str = Field(min_length=1, max_length=50_000)
    input_format: str | None = Field(default=None, max_length=10_000)
    output_format: str | None = Field(default=None, max_length=10_000)
    constraints_text: str | None = Field(default=None, max_length=10_000)
    time_limit_ms: int = Field(ge=50, le=30_000)
    memory_limit_mb: int = Field(ge=16, le=1_024)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        return _normalize_required_text(value, "Problem title", 3, 180)

    @field_validator("statement")
    @classmethod
    def normalize_statement(cls, value: str) -> str:
        return _normalize_required_text(value, "Problem statement", 1, 50_000)

    @field_validator("input_format", "output_format", "constraints_text")
    @classmethod
    def normalize_optional_fields(cls, value: str | None, info) -> str | None:
        return _normalize_optional_text(value, info.field_name.replace("_", " "), 10_000)


class ProblemCreateRequest(ProblemContentRequest):
    slug: str = Field(min_length=3, max_length=120)
    test_cases: list[TestCaseRequest] = Field(min_length=1, max_length=MAX_TEST_CASES)

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str) -> str:
        return _normalize_slug(value)


class ProblemUpdateRequest(ProblemContentRequest):
    """An update writes a complete immutable content snapshot.

    Omit ``test_cases`` to copy the preceding suite into the new suite
    version. Supplying it replaces the suite only for the newly created
    version; existing suites and cases are never changed.
    """

    slug: str | None = Field(default=None, min_length=3, max_length=120)
    test_cases: list[TestCaseRequest] | None = Field(
        default=None, max_length=MAX_TEST_CASES
    )

    @field_validator("slug")
    @classmethod
    def normalize_slug(cls, value: str | None) -> str | None:
        return _normalize_slug(value) if value is not None else None


class TestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ordinal: int
    input_data: str
    expected_output: str
    is_hidden: bool


class PublicTestCaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    ordinal: int
    input_data: str
    expected_output: str


class ProblemResponse(BaseModel):
    id: UUID
    organization_id: UUID
    contest_id: UUID
    created_by: UUID
    slug: str
    is_active: bool
    version_number: int
    title: str
    statement: str
    input_format: str | None
    output_format: str | None
    constraints_text: str | None
    time_limit_ms: int
    memory_limit_mb: int
    created_at: datetime
    updated_at: datetime


class OrganizerProblemResponse(ProblemResponse):
    test_suite_version_number: int
    test_cases: list[TestCaseResponse]


class ParticipantProblemResponse(ProblemResponse):
    test_cases: list[PublicTestCaseResponse]


class ProblemPageResponse(BaseModel):
    items: list[ProblemResponse]
    total: int
    limit: int
    offset: int


class OrganizerProblemPageResponse(BaseModel):
    items: list[OrganizerProblemResponse]
    total: int
    limit: int
    offset: int


class ParticipantProblemPageResponse(BaseModel):
    items: list[ParticipantProblemResponse]
    total: int
    limit: int
    offset: int


class ProblemVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    version_number: int
    title: str
    statement: str
    input_format: str | None
    output_format: str | None
    constraints_text: str | None
    time_limit_ms: int
    memory_limit_mb: int
    created_by: UUID
    created_at: datetime


class ProblemVersionPageResponse(BaseModel):
    items: list[ProblemVersionResponse]
    total: int
    limit: int
    offset: int
