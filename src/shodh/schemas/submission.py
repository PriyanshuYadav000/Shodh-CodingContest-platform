from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from shodh.models.submission import SubmissionStatus, VerdictType


class SubmissionCreateRequest(BaseModel):
    problem_id: UUID
    source_code: str = Field(min_length=1, max_length=200_000)
    language: str = Field(pattern=r"^[a-z0-9_+-]{1,32}$")
    runtime_config: str = Field(default="{}", max_length=10_000)

class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; organization_id: UUID; contest_id: UUID; problem_id: UUID
    problem_version_id: UUID; test_suite_version_id: UUID; user_id: UUID
    source_code: str; language: str; runtime_config: str; status: SubmissionStatus; created_at: datetime

class SubmissionPageResponse(BaseModel):
    items: list[SubmissionResponse]; total: int; limit: int; offset: int

class VerdictCreateRequest(BaseModel):
    verdict: VerdictType
    passed_tests: int = Field(default=0, ge=0)
    total_tests: int = Field(default=0, ge=0)
    execution_time_ms: int | None = Field(default=None, ge=0)
    memory_kb: int | None = Field(default=None, ge=0)
    diagnostics: str | None = Field(default=None, max_length=10_000)

class VerdictResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; submission_id: UUID; attempt_number: int; verdict: VerdictType
    passed_tests: int; total_tests: int; execution_time_ms: int | None; memory_kb: int | None; diagnostics: str | None; created_at: datetime

class LeaderboardEntryResponse(BaseModel):
    user_id: UUID; full_name: str; score: int; penalty_minutes: int; solved: int

class LeaderboardPageResponse(BaseModel):
    items: list[LeaderboardEntryResponse]; total: int; limit: int; offset: int
