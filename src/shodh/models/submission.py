import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from shodh.database.base import Base


class SubmissionStatus(str, enum.Enum):
    QUEUED = "queued"
    JUDGED = "judged"


class VerdictType(str, enum.Enum):
    ACCEPTED = "accepted"
    WRONG_ANSWER = "wrong_answer"
    TIME_LIMIT_EXCEEDED = "time_limit_exceeded"
    MEMORY_LIMIT_EXCEEDED = "memory_limit_exceeded"
    OUTPUT_LIMIT_EXCEEDED = "output_limit_exceeded"
    RUNTIME_ERROR = "runtime_error"
    COMPILATION_ERROR = "compilation_error"
    INFRASTRUCTURE_ERROR = "infrastructure_error"


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (
        Index("ix_submissions_contest_user_created", "contest_id", "user_id", "created_at"),
        Index("ix_submissions_problem_created", "problem_id", "created_at"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False)
    contest_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("contests.id", ondelete="RESTRICT"), nullable=False)
    problem_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problems.id", ondelete="RESTRICT"), nullable=False)
    problem_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("problem_versions.id", ondelete="RESTRICT"), nullable=False)
    test_suite_version_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("test_suite_versions.id", ondelete="RESTRICT"), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    source_code: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(32), nullable=False)
    runtime_config: Mapped[str] = mapped_column(Text, nullable=False, server_default="{}")
    status: Mapped[SubmissionStatus] = mapped_column(Enum(SubmissionStatus, name="submission_status", native_enum=False, create_constraint=True, values_callable=lambda e: [x.value for x in e]), nullable=False, default=SubmissionStatus.QUEUED)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())


class VerdictAttempt(Base):
    __tablename__ = "verdict_attempts"
    __table_args__ = (
        CheckConstraint("attempt_number > 0", name="positive_attempt_number"),
        CheckConstraint("passed_tests >= 0 AND total_tests >= passed_tests", name="valid_test_counts"),
        Index("ix_verdict_attempts_submission_attempt", "submission_id", "attempt_number"),
    )
    id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid.uuid4)
    submission_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("submissions.id", ondelete="RESTRICT"), nullable=False)
    attempt_number: Mapped[int] = mapped_column(Integer, nullable=False)
    verdict: Mapped[VerdictType] = mapped_column(Enum(VerdictType, name="verdict_type", native_enum=False, create_constraint=True, values_callable=lambda e: [x.value for x in e]), nullable=False)
    passed_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    execution_time_ms: Mapped[int | None] = mapped_column(Integer)
    memory_kb: Mapped[int | None] = mapped_column(Integer)
    diagnostics: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default=func.now())
